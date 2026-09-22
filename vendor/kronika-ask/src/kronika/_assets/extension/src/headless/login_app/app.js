// Login wizard client (HE-2d, HE-2f).
//
// Mirrors the engine login step from `/state`, fills native fields and forwards
// them once per submission through `/action`, shows single `/snapshot` images
// for CAPTCHA and the page fallback, and never stores anything: no browser
// storage, no external resource, no inline code, no continuous stream.
//
// HE-2f: a typed `/action` failure (no step progress, fill, or click) is shown
// with its value-free message and automatically switches to the page view so
// the Cooperator can finish the step manually; the header toggle makes the page
// view always reachable.

const statusLine = document.getElementById("status");
const doneButton = document.getElementById("done");
const pageToggle = document.getElementById("page-toggle");
const formView = document.getElementById("form-view");
const captchaView = document.getElementById("captcha-view");
const pageView = document.getElementById("page-view");
const stepTitle = document.getElementById("step-title");
const stepLabels = document.getElementById("step-labels");
const messages = document.getElementById("messages");
const credentialForm = document.getElementById("credential-form");
const valueLabel = document.getElementById("value-label");
const valueInput = document.getElementById("value-input");
const submitButton = document.getElementById("submit");
const captchaActions = document.getElementById("captcha-actions");
const captchaOpen = document.getElementById("captcha-open");
const captchaImage = document.getElementById("captcha-image");
const captchaRefresh = document.getElementById("captcha-refresh");
const captchaPage = document.getElementById("captcha-page");
const pageImage = document.getElementById("page-image");
const pageRefresh = document.getElementById("page-refresh");
const pageCaptcha = document.getElementById("page-captcha");
const pageText = document.getElementById("page-text");
const pageSend = document.getElementById("page-send");

const POLL_MS = 1200;

const PAGE_FALLBACK_CODES = [
  "E_LOGIN_NO_PROGRESS",
  "E_LOGIN_FILL_FAILED",
  "E_LOGIN_CLICK_FAILED",
  "E_DRIVER_FIELD",
  "E_DRIVER_TARGET",
];

const STEP_TITLES = {
  email: "Enter the email address for ChatGPT",
  password: "Enter the password",
  otp: "Enter the one-time code",
  captcha: "Solve the CAPTCHA",
  sso: "External sign-in page",
  unknown: "Unexpected page",
  done: "Login complete - press Done to finish",
};

const FIELD_TYPES = {
  email: { type: "email", label: "Email", mode: "email", autocomplete: "off" },
  password: { type: "password", label: "Password", mode: "text", autocomplete: "off" },
  otp: { type: "text", label: "One-time code", mode: "numeric", autocomplete: "one-time-code" },
};

let current = null;
let step = null;
let view = "form";
let viewLock = null;
let busy = false;
let sessionEnded = false;
let pollTimer = null;

function setStatus(text) {
  statusLine.textContent = text;
}

function setView(name) {
  view = name;
  formView.hidden = name !== "form";
  captchaView.hidden = name !== "captcha";
  pageView.hidden = name !== "page";
  pageToggle.textContent = name === "page" ? "Back" : "Page view";
  if (name === "captcha") refreshCaptcha();
  if (name === "page") refreshPage();
}

function defaultView(state) {
  if (state.step === "captcha") return "captcha";
  if (state.step === "sso" || state.step === "unknown") return "page";
  return "form";
}

function renderMessages(items) {
  const nodes = [];
  for (const text of items) {
    const line = document.createElement("p");
    line.textContent = text;
    nodes.push(line);
  }
  messages.replaceChildren(...nodes);
}

function renderField(state) {
  const field = FIELD_TYPES[state.step];
  if (!field) {
    credentialForm.hidden = true;
    return;
  }
  credentialForm.hidden = false;
  valueLabel.textContent = field.label;
  valueInput.type = field.type;
  valueInput.inputMode = field.mode;
  valueInput.autocomplete = field.autocomplete;
}

function render(state) {
  if (state.step !== step) {
    step = state.step;
    viewLock = null;
    valueInput.value = "";
  }
  current = state;
  stepTitle.textContent = STEP_TITLES[state.step] || STEP_TITLES.unknown;
  stepLabels.textContent = state.labels.join(" | ");
  renderMessages(state.messages);
  const hasCaptchaRegion =
    state.has_captcha && state.captcha_rect !== null && state.captcha_rect !== undefined;
  captchaActions.hidden = !hasCaptchaRegion || state.step === "done";
  pageCaptcha.hidden = !hasCaptchaRegion;
  renderField(state);
  if (state.step === "done") {
    credentialForm.hidden = true;
    captchaActions.hidden = true;
  }
  if (state.step === "captcha" && !hasCaptchaRegion) {
    setView("page");
    return;
  }
  if (!viewLock) setView(defaultView(state));
}

function refreshCaptcha() {
  const rect = current && current.captcha_rect;
  if (!rect) return;
  captchaImage.src =
    "snapshot?x=" + rect.x + "&y=" + rect.y + "&w=" + rect.w + "&h=" + rect.h + "&t=" + Date.now();
}

function refreshPage() {
  pageImage.src = "snapshot?t=" + Date.now();
}

async function postAction(command) {
  if (sessionEnded) return false;
  let response;
  try {
    response = await fetch("action", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
  } catch {
    setStatus("connection lost");
    return false;
  }
  if (response.ok) return true;
  let error = null;
  try {
    const payload = await response.json();
    error = payload && payload.error ? payload.error : null;
  } catch {
    error = null;
  }
  const code = error && typeof error.code === "string" ? error.code : null;
  const message =
    error && typeof error.message === "string" && error.message ? error.message : null;
  if (code && PAGE_FALLBACK_CODES.includes(code)) {
    setStatus((message || code) + " - switched to the page view; continue manually");
    viewLock = step;
    setView("page");
    return false;
  }
  if (message) {
    setStatus(code ? code + ": " + message : message);
    return false;
  }
  setStatus("action failed (" + response.status + ")");
  return false;
}

function mapPoint(event, image, region) {
  const rect = image.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const x = region.x + ((event.clientX - rect.left) / rect.width) * region.w;
  const y = region.y + ((event.clientY - rect.top) / rect.height) * region.h;
  return { x: Math.round(x), y: Math.round(y) };
}

async function forwardClick(event, image, region) {
  const point = mapPoint(event, image, region);
  if (!point) return;
  const ok = await postAction({ type: "click-xy", x: point.x, y: point.y });
  if (ok) setTimeout(() => (image === captchaImage ? refreshCaptcha() : refreshPage()), 800);
}

credentialForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || sessionEnded || !current) return;
  const value = valueInput.value;
  if (!value) return;
  const field = FIELD_TYPES[current.step] ? current.step : null;
  if (!field) return;
  busy = true;
  submitButton.disabled = true;
  const filled = await postAction({ type: "fill", field, value });
  if (filled) {
    if (field === "password" || field === "otp") valueInput.value = "";
    await postAction({ type: "click", target: "submit" });
  }
  busy = false;
  submitButton.disabled = false;
  schedule();
});

captchaImage.addEventListener("click", (event) => {
  if (!current || !current.captcha_rect) return;
  forwardClick(event, captchaImage, {
    x: current.captcha_rect.x,
    y: current.captcha_rect.y,
    w: current.captcha_rect.w,
    h: current.captcha_rect.h,
  });
});

pageImage.addEventListener("click", (event) => {
  const natural = { w: pageImage.naturalWidth, h: pageImage.naturalHeight };
  if (!natural.w || !natural.h) return;
  forwardClick(event, pageImage, { x: 0, y: 0, w: natural.w, h: natural.h });
});

captchaRefresh.addEventListener("click", () => refreshCaptcha());
pageRefresh.addEventListener("click", () => refreshPage());

captchaOpen.addEventListener("click", () => {
  viewLock = step;
  setView("captcha");
});

captchaPage.addEventListener("click", () => {
  viewLock = step;
  setView("page");
});

pageCaptcha.addEventListener("click", () => {
  viewLock = step;
  setView("captcha");
});

pageToggle.addEventListener("click", () => {
  if (view === "page") {
    viewLock = null;
    setView(current ? defaultView(current) : "form");
  } else {
    viewLock = step;
    setView("page");
  }
});

pageSend.addEventListener("click", async () => {
  const value = pageText.value;
  if (!value || sessionEnded) return;
  const ok = await postAction({ type: "fill", field: "focused", value });
  if (ok) pageText.value = "";
});

doneButton.addEventListener("click", async () => {
  if (sessionEnded) return;
  sessionEnded = true;
  doneButton.disabled = true;
  credentialForm.hidden = true;
  captchaActions.hidden = true;
  setStatus("session ended - you can close this tab");
  try {
    await fetch("done", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
  } catch {
    // the server closes the session as it ends
  }
});

function schedule() {
  clearTimeout(pollTimer);
  pollTimer = setTimeout(poll, POLL_MS);
}

async function poll() {
  if (sessionEnded) return;
  if (busy) {
    schedule();
    return;
  }
  try {
    const response = await fetch("state", {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!response.ok) throw new Error(String(response.status));
    const state = await response.json();
    render(state);
    setStatus("connected");
  } catch {
    setStatus("engine unavailable - retrying");
  }
  schedule();
}

poll();
