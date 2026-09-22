(() => {
  const root = (globalThis.ChatGPTCLI = globalThis.ChatGPTCLI || {});
  if (root.domEngine) return;

  function engineError(code, step, message) {
    const error = new Error(message);
    error.code = code;
    error.step = step;
    return error;
  }

  function createDomEngine(ctx) {
    const pack = ctx.pack || {};
    const adapter = root.adapter || {};
    const constants = pack.constants || {
      stability_ms: 2500,
      poll_ms: 500,
      upload_wait_ms: 15000,
    };

    const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const cancelled = () => Boolean(ctx.isCancelled && ctx.isCancelled());
    const normalize = (text) => String(text || "").replace(/\s+/g, " ").trim();
    const sleepTo = (deadline) =>
      delay(Math.min(constants.poll_ms, Math.max(1, deadline - Date.now())));
    const ANSWER_HTML_MAX_CHARS = 1.5 * 1024 * 1024;
    const MODE_TIMEOUT_MS = 5000;
    const CLEAR_TIMEOUT_MS = 2000;
    const VISIBILITY_WAIT_MS = 10000;
    const VISIBILITY_REQUEST_TIMEOUT_MS = 2000;

    function visibleElements(locatorKey, scope) {
      const locator = pack.locators ? pack.locators[locatorKey] : null;
      if (!locator || !Array.isArray(locator.strategies)) return [];
      const found = [];
      for (const strategy of locator.strategies) {
        for (const element of adapter.query(strategy, scope)) {
          if (adapter.isVisible(element)) found.push(element);
        }
      }
      return found;
    }

    function composerHandle() {
      for (const element of visibleElements("composer")) {
        const tag = element.tagName ? element.tagName.toLowerCase() : "";
        if (tag === "div" && element.isContentEditable) {
          return { kind: "contenteditable", element };
        }
        if (tag === "textarea") return { kind: "textarea", element };
      }
      return null;
    }

    function sendControl() {
      const candidates = visibleElements("send");
      return candidates.length > 0 ? candidates[0] : null;
    }

    function stopVisible() {
      return visibleElements("stop_control").length > 0;
    }

    function assistantNodes() {
      const locator = pack.locators ? pack.locators.assistant_message : null;
      if (!locator || !Array.isArray(locator.strategies)) return [];
      const nodes = [];
      for (const strategy of locator.strategies) {
        for (const element of adapter.query(strategy)) {
          if (element && element.isConnected) nodes.push(element);
        }
      }
      return nodes;
    }

    function assistantCount() {
      return assistantNodes().length;
    }

    function extractAnswerText(node) {
      const markdown = node.querySelector ? node.querySelector(".markdown") : null;
      const source = markdown || node;
      return (source.innerText || source.textContent || "").trim();
    }

    /**
     * Return the innerHTML of the same `.markdown` node used for text
     * extraction. This is untrusted page data: the bridge sanitizes it before
     * it is stored. Returns null when the node is absent, empty, or larger
     * than the cap; extraction failure never fails a job.
     */
    function extractAnswerHtml(node) {
      try {
        const markdown =
          node && node.querySelector ? node.querySelector(".markdown") : null;
        if (!markdown || typeof markdown.innerHTML !== "string") return null;
        if (!markdown.innerHTML) return null;
        if (markdown.innerHTML.length > ANSWER_HTML_MAX_CHARS) return null;
        return markdown.innerHTML;
      } catch (error) {
        return null;
      }
    }

    async function locateComposer(options = {}) {
      const requested = Number(options.timeoutMs);
      const timeoutMs =
        Number.isFinite(requested) && requested > 0 ? requested : 15000;
      const deadline = Date.now() + timeoutMs;
      for (;;) {
        if (cancelled()) throw engineError("E_CANCELLED", "locate_composer", "cancelled");
        const handle = composerHandle();
        if (handle) return handle;
        if (Date.now() >= deadline) break;
        await sleepTo(deadline);
      }
      throw engineError(
        "E_COMPOSER_NOT_FOUND",
        "locate_composer",
        "composer not found within " + timeoutMs + " ms"
      );
    }

    function selectAll(element) {
      const selection = window.getSelection();
      if (!selection) return false;
      const range = document.createRange();
      range.selectNodeContents(element);
      selection.removeAllRanges();
      selection.addRange(range);
      return true;
    }

    function composerValue(handle) {
      if (!handle) return "";
      if (handle.kind === "textarea") return String(handle.element.value || "");
      return handle.element.innerText || handle.element.textContent || "";
    }

    function composerEmpty(handle) {
      return normalize(composerValue(handle)) === "";
    }

    async function waitForComposerHandle(timeoutMs) {
      const deadline = Date.now() + timeoutMs;
      for (;;) {
        const handle = composerHandle();
        if (handle) return handle;
        if (Date.now() >= deadline) return null;
        await sleepTo(deadline);
      }
    }

    function webSearchPill(handle) {
      const composer = handle || composerHandle();
      if (!composer) return null;
      const candidates = visibleElements("web_search_pill", composer.element);
      return candidates.length > 0 ? candidates[0] : null;
    }

    function webSearchActive(handle) {
      return webSearchPill(handle) !== null;
    }

    function composerRemainderBeyondPill(handle) {
      const value = normalize(composerValue(handle));
      if (value === "") return "";
      const pill = webSearchPill(handle);
      const pillText = pill ? normalize(pill.textContent) : "";
      if (pillText === "") return value;
      return value.split(pillText).join("").trim();
    }

    function pressEscape() {
      try {
        const selection = window.getSelection();
        if (selection) selection.removeAllRanges();
        const active = document.activeElement;
        for (const target of [document, active]) {
          if (target && typeof target.dispatchEvent === "function") {
            target.dispatchEvent(
              new KeyboardEvent("keydown", {
                key: "Escape",
                code: "Escape",
                bubbles: true,
                cancelable: true,
              })
            );
          }
        }
      } catch (error) {
        return;
      }
    }

    async function clearComposer(options = {}) {
      const requested = Number(options.timeoutMs);
      const timeoutMs =
        Number.isFinite(requested) && requested > 0 ? requested : CLEAR_TIMEOUT_MS;
      const handle = await waitForComposerHandle(timeoutMs);
      if (!handle) {
        throw engineError(
          "E_COMPOSER_NOT_FOUND",
          "clear_composer",
          "composer not found within " + timeoutMs + " ms"
        );
      }
      handle.element.focus();
      if (handle.kind === "contenteditable") {
        selectAll(handle.element);
        document.execCommand("delete");
      } else {
        const descriptor = Object.getOwnPropertyDescriptor(
          HTMLTextAreaElement.prototype,
          "value"
        );
        if (!descriptor || typeof descriptor.set !== "function") {
          throw engineError(
            "E_INPUT_FAILED",
            "clear_composer",
            "textarea value setter is unavailable"
          );
        }
        descriptor.set.call(handle.element, "");
        handle.element.dispatchEvent(new Event("input", { bubbles: true }));
      }
      const deadline = Date.now() + timeoutMs;
      while (!composerEmpty(handle)) {
        if (Date.now() >= deadline) {
          throw engineError(
            "E_INPUT_FAILED",
            "clear_composer",
            "composer text was not cleared"
          );
        }
        await sleepTo(deadline);
      }
      if (handle.kind === "contenteditable" && webSearchActive(handle)) {
        const pill = webSearchPill(handle);
        if (pill) {
          const selection = window.getSelection();
          if (selection) {
            const range = document.createRange();
            range.selectNode(pill);
            selection.removeAllRanges();
            selection.addRange(range);
            document.execCommand("delete");
          }
        }
        const pillDeadline = Date.now() + timeoutMs;
        while (webSearchActive(handle)) {
          if (Date.now() >= pillDeadline) {
            throw engineError(
              "E_INPUT_FAILED",
              "clear_composer",
              "composer still holds the web-search pill"
            );
          }
          await sleepTo(pillDeadline);
        }
      }
    }

    async function enableWebSearch() {
      throw engineError(
        "E_WEB_SEARCH_UNAVAILABLE",
        "mode",
        "web search is not available in this build"
      );
    }

    async function insertPrompt(text, options = {}) {
      if (options && options.webSearch === true) {
        throw engineError(
          "E_WEB_SEARCH_UNAVAILABLE",
          "mode",
          "web search is not available in this build"
        );
      }
      const webSearch = false;
      await clearComposer();
      const handle = await locateComposer();
      if (webSearch) {
        if (!webSearchActive(handle)) {
          throw engineError(
            "E_WEB_SEARCH_UNAVAILABLE",
            "insert_prompt",
            "web-search pill is not active before insertion"
          );
        }
        const remainder = composerRemainderBeyondPill(handle);
        if (remainder !== "") {
          throw engineError(
            "E_INPUT_FAILED",
            "insert_prompt",
            "composer contains unexpected pre-existing content: " + remainder
          );
        }
      } else if (!composerEmpty(handle)) {
        throw engineError(
          "E_INPUT_FAILED",
          "insert_prompt",
          "composer is not empty"
        );
      }
      if (handle.kind === "contenteditable") {
        handle.element.focus();
        const selection = window.getSelection();
        if (!selection) {
          throw engineError(
            "E_INPUT_FAILED",
            "insert_prompt",
            "selection is unavailable"
          );
        }
        const range = document.createRange();
        range.selectNodeContents(handle.element);
        range.collapse(false);
        selection.removeAllRanges();
        selection.addRange(range);
        const inserted = document.execCommand("insertText", false, text);
        if (!inserted) {
          throw engineError(
            "E_INPUT_FAILED",
            "insert_prompt",
            "insertText was rejected by the page"
          );
        }
      } else {
        const descriptor = Object.getOwnPropertyDescriptor(
          HTMLTextAreaElement.prototype,
          "value"
        );
        if (!descriptor || typeof descriptor.set !== "function") {
          throw engineError(
            "E_INPUT_FAILED",
            "insert_prompt",
            "textarea value setter is unavailable"
          );
        }
        descriptor.set.call(handle.element, text);
        handle.element.dispatchEvent(new Event("input", { bubbles: true }));
      }
      const observed = normalize(composerValue(handle));
      if (!observed.includes(normalize(text))) {
        throw engineError(
          "E_INPUT_FAILED",
          "insert_prompt",
          "composer text does not contain the prompt"
        );
      }
      if (webSearch && !webSearchActive(handle)) {
        throw engineError(
          "E_WEB_SEARCH_UNAVAILABLE",
          "insert_prompt",
          "the web-search pill was lost during insertion"
        );
      }
    }

    async function waitFor(predicate, timeoutMs, step) {
      const deadline = Date.now() + timeoutMs;
      for (;;) {
        if (cancelled()) throw engineError("E_CANCELLED", step, "cancelled");
        const value = predicate();
        if (value) return value;
        if (Date.now() >= deadline) return null;
        await sleepTo(deadline);
      }
    }

    async function submit() {
      const ready = await waitFor(
        () => {
          const control = sendControl();
          if (!control) return null;
          if (control.getAttribute("aria-disabled") === "true") return null;
          if (control.disabled) return null;
          return control;
        },
        10000,
        "submit"
      );
      if (!ready) {
        throw engineError(
          "E_SEND_NOT_READY",
          "submit",
          "send control never became ready"
        );
      }
      const baseline = assistantCount();
      ready.click();
      const accepted = await waitFor(
        () => {
          const control = sendControl();
          const controlGone =
            !control ||
            control.disabled ||
            control.getAttribute("aria-disabled") === "true";
          const grew = assistantCount() > baseline;
          return controlGone || grew ? true : null;
        },
        10000,
        "submit"
      );
      if (!accepted) {
        throw engineError("E_SEND_FAILED", "submit", "send click was not accepted");
      }
      return { baseline };
    }

    function documentVisible() {
      return document.visibilityState === "visible";
    }

    function announceExtractionDone() {
      try {
        if (!(globalThis.chrome && chrome.runtime && chrome.runtime.sendMessage)) {
          return;
        }
        chrome.runtime
          .sendMessage({ type: "extraction_done", job_id: ctx.jobId || null })
          .catch(() => null);
      } catch (error) {
        return;
      }
    }

    function requestEnsureVisible() {
      return new Promise((resolve) => {
        let settled = false;
        const settle = (value) => {
          if (settled) return;
          settled = true;
          resolve(value);
        };
        try {
          if (!(globalThis.chrome && chrome.runtime && chrome.runtime.sendMessage)) {
            settle(false);
            return;
          }
          const timer = setTimeout(
            () => settle(false),
            VISIBILITY_REQUEST_TIMEOUT_MS
          );
          Promise.resolve(
            chrome.runtime.sendMessage({
              type: "ensure_visible",
              job_id: ctx.jobId || null,
            })
          ).then(
            (response) => {
              clearTimeout(timer);
              settle(Boolean(response && response.ok));
            },
            () => {
              clearTimeout(timer);
              settle(false);
            }
          );
        } catch (error) {
          settle(false);
        }
      });
    }

    async function ensureVisibleDocument() {
      if (documentVisible()) return true;
      const deadline = Date.now() + VISIBILITY_WAIT_MS;
      await requestEnsureVisible();
      for (;;) {
        if (documentVisible()) return true;
        if (cancelled()) {
          throw engineError("E_CANCELLED", "observe", "cancelled");
        }
        if (Date.now() >= deadline) return false;
        await delay(Math.min(constants.poll_ms, Math.max(1, deadline - Date.now())));
      }
    }

    async function confirmHiddenAnswer(node, text) {
      const visible = await ensureVisibleDocument();
      if (!visible) {
        throw engineError(
          "E_RESPONSE_TIMEOUT",
          "observe",
          "document stayed hidden; the answer could not be confirmed"
        );
      }
      if (extractAnswerText(node) !== text) return null;
      if (stopVisible()) return null;
      const confirmDeadline = Date.now() + constants.poll_ms;
      while (Date.now() < confirmDeadline) {
        if (cancelled()) {
          throw engineError("E_CANCELLED", "observe", "cancelled");
        }
        await delay(
          Math.min(constants.poll_ms, Math.max(1, confirmDeadline - Date.now()))
        );
      }
      if (!documentVisible()) return null;
      if (extractAnswerText(node) !== text) return null;
      if (stopVisible()) return null;
      return {
        text,
        html: extractAnswerHtml(node),
        url: location.href,
      };
    }

    async function observeAnswer(options = {}) {
      const baseline =
        typeof options.baseline === "number" ? options.baseline : assistantCount();
      const requested = Number(options.deadlineMs);
      const deadline =
        Number.isFinite(requested) && requested > 0
          ? Date.now() + requested
          : Date.now() + 600000;
      let lastText = null;
      let lastChange = Date.now();
      let lastStop = false;
      let started = false;
      let visibilityRequested = false;
      try {
        for (;;) {
          if (cancelled()) throw engineError("E_CANCELLED", "observe", "cancelled");
          const nodes = assistantNodes();
          if (nodes.length > baseline) {
            started = true;
            const node = nodes[nodes.length - 1];
            const text = extractAnswerText(node);
            const stop = stopVisible();
            const now = Date.now();
            if (stop !== lastStop) {
              lastStop = stop;
              lastChange = now;
            }
            if (text !== lastText) {
              lastText = text;
              lastChange = now;
            } else if (!stop && text && now - lastChange >= constants.stability_ms) {
              if (documentVisible()) {
                return {
                  text,
                  html: extractAnswerHtml(node),
                  url: location.href,
                };
              }
              visibilityRequested = true;
              const confirmed = await confirmHiddenAnswer(node, text);
              if (confirmed) return confirmed;
              lastChange = Date.now();
            } else if (
              !stop &&
              !text &&
              now - lastChange >= constants.stability_ms * 2
            ) {
              throw engineError(
                "E_RESPONSE_EMPTY",
                "observe",
                "assistant message stayed empty"
              );
            }
          }
          if (Date.now() >= deadline) break;
          await sleepTo(deadline);
        }
        if (!started) {
          throw engineError(
            "E_RESPONSE_TIMEOUT",
            "observe",
            "no assistant message appeared before the deadline"
          );
        }
        throw engineError(
          "E_RESPONSE_TIMEOUT",
          "observe",
          "answer did not stabilize before the deadline"
        );
      } finally {
        if (visibilityRequested) announceExtractionDone();
      }
    }

    async function startNewChat() {
      const deadline = Date.now() + 5000;
      while (Date.now() < deadline) {
        if (cancelled()) throw engineError("E_CANCELLED", "new_chat", "cancelled");
        const button = document.querySelector(
          '[data-testid="create-new-chat-button"]'
        );
        if (button && adapter.isVisible(button)) {
          button.click();
          await delay(300);
          return;
        }
        await delay(200);
      }
      throw engineError(
        "E_INTERNAL",
        "new_chat",
        "create-new-chat control not found within 5000 ms"
      );
    }

    /**
     * Parse a bridge-provided project object into a same-origin project URL
     * and its `g-p-...` path token. Returns null for anything that is not a
     * chatgpt.com project URL; no page state is read.
     */
    function parseProject(project) {
      const url = project && typeof project.url === "string" ? project.url : "";
      let parsed = null;
      try {
        parsed = new URL(url);
      } catch (error) {
        return null;
      }
      if (parsed.origin !== "https://chatgpt.com") return null;
      const segments = parsed.pathname.split("/").filter(Boolean);
      const token = segments.length > 1 ? segments[1] : "";
      if (segments[0] !== "g" || !token.startsWith("g-p-") || token.length <= 4) {
        return null;
      }
      return { url: parsed.href, token, pathname: parsed.pathname };
    }

    /**
     * Containment check only. Tab navigation belongs to the service worker, so
     * the content script never navigates; this returns whether the current
     * pathname carries the project's `g-p-...` token.
     */
    function assertProject(project) {
      const parsed = parseProject(project);
      if (!parsed) return false;
      return location.pathname.includes(parsed.token);
    }

    async function classifyIntervention() {
      if (root.interventions && typeof root.interventions.classify === "function") {
        return root.interventions.classify(ctx);
      }
      return null;
    }

    /**
     * Attach bridge-provided files through the upload input. File upload is
     * permanently unavailable in this build and reports the frozen
     * E_UPLOAD_FAILED code instead of a raw DOM error.
     */
    async function uploadFiles() {
      throw engineError(
        "E_UPLOAD_FAILED",
        "upload",
        "file upload is not available in this build"
      );
    }

    /**
     * Read-only locator probe. The S1 adapter provides the minimal probe set;
     * the full per-job probe surface arrives in S3.
     */
    async function probe() {
      if (typeof adapter.probe === "function") return adapter.probe(pack);
      return [];
    }

    return {
      locateComposer,
      clearComposer,
      enableWebSearch,
      webSearchActive,
      insertPrompt,
      submit,
      observeAnswer,
      extractAnswerHtml,
      classifyIntervention,
      startNewChat,
      assertProject,
      uploadFiles,
      probe,
    };
  }

  root.domEngine = { createDomEngine, engineError };
})();
