const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const REPO = path.resolve(__dirname, "..");
const companion = require(path.join(REPO, "extension/shared/messages.js"));
const contract = require(path.join(REPO, "extension/content/x_adapter_contract_v1.js"));
const adapterSource = fs.readFileSync(
  path.join(REPO, "extension/content/x_adapter.js"),
  "utf8"
);
const workerSource = fs.readFileSync(
  path.join(REPO, "extension/background/service_worker.js"),
  "utf8"
);
const manifest = JSON.parse(
  fs.readFileSync(path.join(REPO, "extension/manifest.json"), "utf8")
);

test("unknown protocol versions and types are dropped", () => {
  assert.equal(companion.dropUnknown({ v: "other", type: companion.TYPES.SAVE_POST }), null);
  assert.equal(companion.dropUnknown({ v: companion.PROTOCOL, type: "proxy_fetch" }), null);
  assert.equal(companion.dropUnknown({ url: "https://evil.example" }), null);
  assert.ok(
    companion.dropUnknown({
      v: companion.PROTOCOL,
      type: companion.TYPES.SAVE_POST,
      payload: { url: "https://x.com/a/status/1" },
    })
  );
});

test("service worker path templates reject caller-supplied URLs and ids", () => {
  assert.equal(companion.pathFor("content", { mediaId: "https://evil.example", locationId: "x" }), null);
  assert.equal(companion.pathFor("xRequest", { claimId: "../etc/passwd" }), null);
  assert.equal(
    companion.pathFor("content", {
      mediaId: "11111111-1111-4111-8111-111111111111",
      locationId: "22222222-2222-4222-8222-222222222222",
    }),
    "/api/media/11111111-1111-4111-8111-111111111111/locations/22222222-2222-4222-8222-222222222222/content"
  );
  assert.equal(companion.pathFor("identity"), "/api/identity/me");
  assert.match(workerSource, /pathFor\(/);
  assert.doesNotMatch(workerSource, /fetch\(payload\.url\)/);
  assert.doesNotMatch(workerSource, /fetch\(message\.url\)/);
});

test("X URL allowlist accepts only public https post permalinks", () => {
  assert.ok(companion.acceptXPostUrl("https://x.com/fixture/status/123456789"));
  assert.equal(companion.acceptXPostUrl("https://evil.example/fixture/status/123456789"), null);
  assert.equal(companion.acceptXPostUrl("https://x.com/i/web/status/123456789"), null);
  assert.equal(companion.acceptXPostUrl("https://x.com/fixture/status/123456789?foo=1"), null);
});

test("adapter contract has no Post-button or auto-submit path", () => {
  const serialized = JSON.stringify(contract);
  assert.equal(serialized.includes("tweetButton"), false);
  assert.equal("postButton" in contract, false);
  assert.doesNotMatch(adapterSource, /tweetButton/);
  assert.doesNotMatch(adapterSource, /form\.submit/);
  assert.doesNotMatch(adapterSource, /dispatchEvent\(new Event\(["']submit/);
  assert.match(adapterSource, /DataTransfer/);
  assert.match(adapterSource, /pollClaim/);
  assert.match(adapterSource, /RECOVER_INFLIGHT/);
});

test("manifest permissions stay minimized and omit X host access", () => {
  assert.deepEqual(manifest.permissions.sort(), ["sidePanel", "storage"]);
  assert.deepEqual(manifest.optional_permissions, ["downloads"]);
  assert.deepEqual(manifest.optional_host_permissions, ["https://*.ts.net/*"]);
  assert.equal("host_permissions" in manifest, false);
  assert.equal("externally_connectable" in manifest, false);
  assert.equal((manifest.permissions || []).includes("tabs"), false);
  assert.equal((manifest.permissions || []).includes("alarms"), false);
  assert.equal((manifest.permissions || []).includes("cookies"), false);
  const matches = manifest.content_scripts[0].matches.sort();
  assert.deepEqual(matches, ["https://twitter.com/*", "https://x.com/*"]);
});

test("chunk reassembly stays bounded", () => {
  const first = companion.bytesFromBase64(Buffer.from("abc").toString("base64"));
  const second = companion.bytesFromBase64(Buffer.from("def").toString("base64"));
  const joined = companion.concatChunks([first, second], 6);
  assert.equal(Buffer.from(joined).toString(), "abcdef");
  assert.equal(companion.MAX_ATTACH_BYTES, 32 * 1024 * 1024);
});

test("service worker recovers inflight claim ids from storage", () => {
  assert.match(workerSource, /inflightClaims/);
  assert.match(workerSource, /RECOVER_INFLIGHT/);
  assert.doesNotMatch(workerSource, /setInterval/);
});

test("adapter contract exposes frozen action-bar, Share, and media-host selectors", () => {
  assert.equal(contract.adapterVersion, 1);
  assert.ok(Object.isFrozen(contract.actionGroupSelectors));
  assert.ok(Object.isFrozen(contract.actionBarSignals));
  assert.ok(Object.isFrozen(contract.shareSelectors));
  assert.ok(Object.isFrozen(contract.mediaHostSelectors));
  assert.ok(Object.isFrozen(contract.composerChromeSelectors));
  assert.ok(Object.isFrozen(contract.composerMediaButtonSelectors));
  assert.deepEqual(contract.actionGroupSelectors, ["[role='group']"]);
  assert.deepEqual(contract.actionBarSignals, [
    "[data-testid='reply']",
    "[data-testid='retweet']",
    "[data-testid='like']",
  ]);
  assert.deepEqual(contract.shareSelectors, [
    "[data-testid='share']",
    "[aria-label='Share post']",
    "[aria-label='Share']",
  ]);
  assert.deepEqual(contract.mediaHostSelectors, [
    "[data-testid='tweetPhoto']",
    "[data-testid='videoPlayer']",
    "[data-testid='videoComponent']",
    "[data-framenest-media]",
  ]);
  assert.deepEqual(contract.composerChromeSelectors, ["[data-framenest-composer-chrome]"]);
  assert.ok(Object.isFrozen(contract.composerTextRowSelectors));
  assert.deepEqual(contract.composerTextRowSelectors, ["[data-framenest-composer-text-row]"]);
  assert.ok(contract.composerRoots.includes("[aria-label='Post your reply']"));
  assert.deepEqual(contract.composerMediaButtonSelectors, [
    "[data-testid='fileInput']",
    "[aria-label='Add photos or video']",
    "[aria-label='Media']",
  ]);
});

test("in-feed Save is a per-media hover overlay, not an action-row control", () => {
  const fixture = fs.readFileSync(
    path.join(REPO, "tests/support/x_fixtures/composer.html"),
    "utf8"
  );
  assert.match(fixture, /role="group"/);
  assert.match(fixture, /data-testid="reply"/);
  assert.match(fixture, /data-testid="retweet"/);
  assert.match(fixture, /data-testid="like"/);
  assert.match(fixture, /aria-label="Share post"/);
  assert.match(fixture, /data-testid="tweetPhoto"/);
  assert.match(fixture, /data-framenest-media/);
  assert.doesNotMatch(fixture, /data-framenest-companion/);

  assert.doesNotMatch(adapterSource, /writing-mode/);
  assert.doesNotMatch(adapterSource, /addButton\(\s*postRoot/);
  assert.doesNotMatch(adapterSource, /postRoot\.appendChild/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*result/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Save to FrameNest["']/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Saving/);
  assert.doesNotMatch(adapterSource, /ownActionGroup/);
  assert.doesNotMatch(adapterSource, /shareActionColumn/);
  assert.doesNotMatch(adapterSource, /SAVE_DOWN_NUDGE/);
  assert.doesNotMatch(adapterSource, /insertAdjacentElement\("afterend"/);
  assert.doesNotMatch(adapterSource, /return "missing_bar"/);
  assert.doesNotMatch(adapterSource, /return "missing_share"/);
  assert.doesNotMatch(adapterSource, /adapter_drift/);
  assert.doesNotMatch(adapterSource, /style\.background = "transparent"/);
  assert.doesNotMatch(
    adapterSource,
    /\[data-framenest-companion='save'\][\s\S]{0,500}background:\s*transparent/
  );
  assert.match(adapterSource, /setAttribute\("data-framenest-companion", "save"\)/);
  assert.match(adapterSource, /setAttribute\("aria-label", name\)/);
  assert.match(adapterSource, /stopImmediatePropagation/);
  assert.match(adapterSource, /ownMediaHosts/);
  assert.match(adapterSource, /mediaHostSelectors/);
  assert.match(adapterSource, /data-framenest-media-host/);
  assert.match(adapterSource, /data-framenest-companion-style/);
  assert.match(adapterSource, /position: absolute/);
  const saveRule = adapterSource.match(
    /\[data-framenest-companion='save'\] \{[\s\S]*?\n\}/
  );
  assert.ok(saveRule);
  assert.match(saveRule[0], /bottom:\s*0/);
  assert.match(saveRule[0], /right:\s*0/);
  assert.doesNotMatch(saveRule[0], /top:\s*0/);
  assert.doesNotMatch(saveRule[0], /left:\s*0/);
  assert.doesNotMatch(adapterSource, /\[data-framenest-companion='save'\][\s\S]{0,80}top:\s*0/);
  assert.doesNotMatch(adapterSource, /\[data-framenest-companion='save'\][\s\S]{0,80}left:\s*0/);
  assert.match(adapterSource, /opacity: 0/);
  assert.match(adapterSource, /pointer-events: none/);
  assert.match(adapterSource, /background: #000000/);
  assert.match(adapterSource, /style\.position = "relative"/);
  assert.match(adapterSource, /return "no_media"/);
  assert.match(adapterSource, /TYPES\.SAVE_POST/);
  assert.match(adapterSource, /accepted\.submittedUrl/);
  assert.doesNotMatch(adapterSource, /pbs\.twimg\.com/);
  assert.match(adapterSource, /data-framenest-companion"\) === "save"/);
  assert.match(adapterSource, /Save to FrameNest failed/);
  assert.match(adapterSource, /TYPES\.SAVE_POST, \{\s*url: accepted\.submittedUrl/);
  assert.doesNotMatch(adapterSource, /M8 8l8 8/);
  assert.doesNotMatch(adapterSource, /M16 8l-8 8/);
  assert.match(adapterSource, /kind === "failed"[\s\S]{0,160}M12 6\.5v11M6\.5 12h11/);
});

test("companion surfaces copy FrameNest gallery visual tokens", () => {
  const pickerCss = fs.readFileSync(path.join(REPO, "extension/ui/picker.css"), "utf8");
  const pickerHtml = fs.readFileSync(path.join(REPO, "extension/ui/picker.html"), "utf8");
  const pickerJs = fs.readFileSync(path.join(REPO, "extension/ui/picker.js"), "utf8");
  const tokenNames = [
    "--background",
    "--surface",
    "--surface-input",
    "--text",
    "--text-muted",
    "--text-soft",
    "--accent",
    "--accent-strong",
    "--accent-soft",
    "--accent-border",
    "--accent-glow",
    "--danger",
    "--focus",
    "--radius-sm",
    "--font-mono",
  ];
  tokenNames.forEach((token) => {
    assert.match(pickerCss, new RegExp(token.replace(/-/g, "\\-")));
  });
  assert.match(pickerCss, /#00ff41/);
  assert.match(pickerCss, /#39ff14/);
  assert.match(adapterSource, /#00ff41/);
  assert.match(adapterSource, /#39ff14/);
  assert.doesNotMatch(adapterSource, /copyActionColor/);
  assert.doesNotMatch(adapterSource, /getComputedStyle\([^)]+\)\.color/);
  assert.doesNotMatch(adapterSource, /rgba\(127, 127, 127, 0\.12\)/);
  assert.match(adapterSource, /GALLERY_ACCENT/);
  assert.match(pickerHtml, /header-search__control/);
  assert.match(pickerHtml, /header-search__prompt/);
  assert.match(pickerHtml, /id="preview"/);
  assert.match(pickerHtml, /id="preview-prev"/);
  assert.match(pickerHtml, /id="preview-next"/);
  assert.doesNotMatch(pickerJs, /innerHTML/);
  assert.doesNotMatch(pickerJs, /form\.submit/);
});

test("Attach floats on the focused reply field and opens an in-page popup", () => {
  const fixture = fs.readFileSync(
    path.join(REPO, "tests/support/x_fixtures/composer.html"),
    "utf8"
  );
  assert.ok(Object.isFrozen(contract.composerToolbarSelectors));
  assert.deepEqual(contract.composerToolbarSelectors, [
    "[data-testid='toolBar']",
    "[data-framenest-composer-toolbar]",
    "[role='toolbar']",
  ]);
  assert.ok(Object.isFrozen(contract.contentDisclosureSelectors));
  assert.deepEqual(contract.contentDisclosureSelectors, [
    "[aria-label='Content disclosure']",
    "[data-framenest-content-disclosure]",
  ]);
  assert.ok(Object.isFrozen(contract.bookmarkSelectors));
  assert.match(fixture, /data-testid="toolBar"/);
  assert.match(fixture, /data-framenest-composer-toolbar/);
  assert.match(fixture, /data-framenest-composer-chrome/);
  assert.match(fixture, /data-framenest-composer-text-row/);
  assert.match(fixture, /data-framenest-composer-row-canary/);
  assert.match(fixture, /id="inline-reply-only-editable"/);
  assert.match(fixture, /id="inline-reply-deep"/);
  assert.match(fixture, /Post your reply/);
  const inlineOnly = fixture.slice(
    fixture.indexOf('id="inline-reply-only-editable"'),
    fixture.indexOf('id="inline-reply-deep"')
  );
  assert.doesNotMatch(inlineOnly, /data-framenest-composer-text-row/);
  assert.doesNotMatch(inlineOnly, /data-framenest-composer-chrome/);
  assert.match(inlineOnly, /contenteditable="true"/);
  assert.match(inlineOnly, /data-testid="toolBar"/);
  assert.match(fixture, /data-testid="bookmark"/);
  assert.match(fixture, /aria-label="Content disclosure"/);
  assert.match(fixture, /data-framenest-content-disclosure/);
  assert.doesNotMatch(adapterSource, /addButton\(/);
  assert.doesNotMatch(adapterSource, /composerRoot\.appendChild/);
  assert.doesNotMatch(adapterSource, /composerChrome\.appendChild/);
  assert.doesNotMatch(adapterSource, /textRow\.appendChild/);
  assert.doesNotMatch(adapterSource, /ensureContainingBlock\(textRow\)/);
  assert.doesNotMatch(adapterSource, /insertAttachAfterDisclosure/);
  assert.doesNotMatch(adapterSource, /findContentDisclosure/);
  assert.doesNotMatch(adapterSource, /disclosureActionColumn/);
  assert.doesNotMatch(adapterSource, /tweetButton/);
  assert.doesNotMatch(adapterSource, /form\.submit/);
  assert.doesNotMatch(adapterSource, /dispatchEvent\(new Event\(["']submit/);
  assert.doesNotMatch(adapterSource, /openPicker/);
  assert.doesNotMatch(adapterSource, /sidePanel/);
  assert.doesNotMatch(adapterSource, /\bfetch\s*\(/);
  assert.match(adapterSource, /findComposerChrome/);
  assert.match(adapterSource, /findComposerTextRow/);
  assert.match(adapterSource, /composerChromeSelectors/);
  assert.match(adapterSource, /composerTextRowSelectors/);
  assert.match(adapterSource, /setAttribute\("data-framenest-companion", "attach"\)/);
  assert.match(adapterSource, /setAttribute\("aria-label", ATTACH_NAME\)/);
  assert.match(adapterSource, /document\.documentElement\.appendChild\(button\)/);
  assert.match(adapterSource, /addEventListener\("focusin", show, true\)/);
  assert.match(adapterSource, /addEventListener\("focus", show, true\)/);
  assert.match(adapterSource, /addEventListener\("focusin", onComposerFocusIn, true\)/);
  assert.match(adapterSource, /addEventListener\("scroll", repositionVisibleAttaches, true\)/);
  assert.match(adapterSource, /data-framenest-attach-visible/);
  assert.match(adapterSource, /data-framenest-companion-popup-host/);
  assert.match(adapterSource, /attachShadow\(\{\s*mode:\s*"closed"\s*\}\)/);
  assert.match(adapterSource, /getURL\("ui\/picker\.html"\)/);
  assert.match(adapterSource, /getBoundingClientRect/);
  assert.match(adapterSource, /enoughAbove/);
  assert.match(adapterSource, /::-webkit-inner-spin-button/);
  assert.match(adapterSource, /::-webkit-outer-spin-button/);
  const attachRule = adapterSource.match(
    /\[data-framenest-companion='attach'\] \{[\s\S]*?\n\}/
  );
  assert.ok(attachRule);
  assert.match(attachRule[0], /position:\s*fixed/);
  assert.doesNotMatch(attachRule[0], /position:\s*absolute/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*["']Attach from FrameNest["']/);
  assert.doesNotMatch(adapterSource, /textContent\s*=\s*ATTACH_NAME/);
  assert.doesNotMatch(
    adapterSource,
    /\[data-framenest-composer[^\]]*\]:hover[^\n]*\[data-framenest-companion='attach'\]/
  );
});

test("in-page picker iframe WAR is match-limited to X hosts", () => {
  const dumped = JSON.stringify(manifest);
  assert.equal(dumped.includes("<all_urls>"), false);
  const war = manifest.web_accessible_resources;
  assert.ok(Array.isArray(war));
  assert.equal(war.length, 1);
  const entry = war[0];
  assert.deepEqual(entry.matches.slice().sort(), ["https://twitter.com/*", "https://x.com/*"]);
  assert.equal(entry.matches.join(" ").includes("ts.net"), false);
  assert.deepEqual(entry.resources.slice().sort(), [
    "ui/picker.css",
    "ui/picker.html",
    "ui/picker.js",
  ]);
});

test("picker is search-first with a Settings Origin sheet", () => {
  const pickerHtml = fs.readFileSync(path.join(REPO, "extension/ui/picker.html"), "utf8");
  const pickerJs = fs.readFileSync(path.join(REPO, "extension/ui/picker.js"), "utf8");
  const pickerCss = fs.readFileSync(path.join(REPO, "extension/ui/picker.css"), "utf8");
  assert.doesNotMatch(pickerHtml, /Search titles/);
  assert.doesNotMatch(pickerJs, /Search titles/);
  assert.doesNotMatch(pickerHtml, /class="picker-brand"/);
  assert.doesNotMatch(pickerHtml, /class="brand-mark"/);
  assert.doesNotMatch(pickerHtml, /<h1>FrameNest<\/h1>/);
  assert.doesNotMatch(pickerHtml, />FN<\/span>/);
  assert.match(pickerHtml, /Search memes/);
  assert.match(pickerHtml, /aria-label="Settings"/);
  assert.match(pickerHtml, /id="settings-tab-origin"/);
  assert.match(pickerHtml, /id="settings-dialog"/);
  assert.match(pickerHtml, /class="settings-dialog"/);
  assert.match(pickerHtml, /role="tablist"/);
  assert.match(pickerCss, /--surface-solid:/);
  assert.match(pickerCss, /--line:/);
  assert.match(pickerCss, /--radius-lg:/);
  assert.match(pickerCss, /--shadow-deep:/);
  assert.match(pickerCss, /--danger-soft:/);
  assert.match(pickerCss, /--transition-fast:/);
  assert.match(pickerCss, /\.settings-dialog__tab--active/);
  assert.match(pickerJs, /showModal/);
  assert.match(pickerJs, /openSettings/);
  assert.match(pickerJs, /closeSettings/);
  assert.match(pickerJs, /renderConnection/);
  assert.doesNotMatch(pickerJs, /innerHTML/);
  assert.doesNotMatch(pickerJs, /form\.submit/);
  assert.doesNotMatch(adapterSource, /tweetButton/);
});

function createMiniDom() {
  class MiniEl {
    constructor(tag, attrs) {
      this.tagName = String(tag).toUpperCase();
      this.attrs = {};
      Object.keys(attrs || {}).forEach((key) => {
        this.attrs[key] = String(attrs[key]);
      });
      this.parentElement = null;
      this.parentNode = null;
      this.childNodes = [];
      this.style = {};
      this.dataset = {};
      this.ownerDocument = null;
    }

    get children() {
      return this.childNodes.filter((node) => node && node.tagName);
    }

    getAttribute(name) {
      if (!Object.prototype.hasOwnProperty.call(this.attrs, name)) {
        return null;
      }
      return this.attrs[name];
    }

    setAttribute(name, value) {
      this.attrs[name] = String(value);
    }

    removeAttribute(name) {
      delete this.attrs[name];
    }

    hasAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attrs, name);
    }

    getBoundingClientRect() {
      return { top: 0, left: 0, right: 120, bottom: 40, width: 120, height: 40, x: 0, y: 0 };
    }

    matches(selector) {
      return matchesSelector(this, selector);
    }

    querySelector(selector) {
      return this.querySelectorAll(selector)[0] || null;
    }

    querySelectorAll(selector) {
      const out = [];
      const visit = (node) => {
        node.children.forEach((child) => {
          if (matchesSelector(child, selector)) {
            out.push(child);
          }
          visit(child);
        });
      };
      visit(this);
      return out;
    }

    contains(other) {
      if (other === this) {
        return true;
      }
      let node = other;
      while (node) {
        if (node === this) {
          return true;
        }
        node = node.parentElement;
      }
      return false;
    }

    appendChild(child) {
      if (child.parentElement) {
        child.parentElement.removeChild(child);
      }
      child.parentElement = this;
      child.parentNode = this;
      child.ownerDocument = this.ownerDocument;
      this.childNodes.push(child);
      return child;
    }

    removeChild(child) {
      const index = this.childNodes.indexOf(child);
      if (index >= 0) {
        this.childNodes.splice(index, 1);
      }
      child.parentElement = null;
      child.parentNode = null;
      return child;
    }

    addEventListener() {}

    removeEventListener() {}
  }

  function matchesSelector(el, selector) {
    let rest = String(selector).trim();
    const tagMatch = rest.match(/^([a-zA-Z][\w-]*)/);
    if (tagMatch) {
      if (el.tagName !== tagMatch[1].toUpperCase()) {
        return false;
      }
      rest = rest.slice(tagMatch[1].length);
    }
    const attrRe = /\[([^\]]+)\]/g;
    let attr;
    let sawAttr = false;
    while ((attr = attrRe.exec(rest))) {
      sawAttr = true;
      const body = attr[1];
      const opMatch = body.match(/^([^\s=~^$*|]+)\s*(\*=|=)\s*(.*)$/);
      if (opMatch) {
        const name = opMatch[1];
        const op = opMatch[2];
        let value = opMatch[3].trim();
        if (
          (value.startsWith("'") && value.endsWith("'")) ||
          (value.startsWith('"') && value.endsWith('"'))
        ) {
          value = value.slice(1, -1);
        }
        const actual = el.getAttribute(name);
        if (op === "=" && actual !== value) {
          return false;
        }
        if (op === "*=" && (!actual || !actual.includes(value))) {
          return false;
        }
      } else if (el.getAttribute(body.trim()) == null) {
        return false;
      }
    }
    return Boolean(tagMatch || sawAttr);
  }

  const documentElement = new MiniEl("html");
  const body = new MiniEl("body");
  const documentRef = {
    documentElement,
    body,
    contains(node) {
      if (!node) {
        return false;
      }
      if (node === documentRef || node === documentElement || node === body) {
        return true;
      }
      return documentElement.contains(node);
    },
    createElement(tag) {
      const node = new MiniEl(tag);
      node.ownerDocument = documentRef;
      return node;
    },
    createElementNS(_ns, tag) {
      const node = new MiniEl(tag);
      node.ownerDocument = documentRef;
      return node;
    },
    querySelector(selector) {
      return documentElement.querySelector(selector);
    },
    querySelectorAll(selector) {
      return documentElement.querySelectorAll(selector);
    },
    addEventListener() {},
    removeEventListener() {},
  };
  documentElement.ownerDocument = documentRef;
  body.ownerDocument = documentRef;
  documentElement.appendChild(body);
  const windowRef = {
    document: documentRef,
    getComputedStyle() {
      return { position: "relative" };
    },
    setTimeout() {
      return 0;
    },
    addEventListener() {},
    removeEventListener() {},
  };
  return { MiniEl, document: documentRef, window: windowRef, body };
}

function el(dom, tag, attrs, children) {
  const node = new dom.MiniEl(tag, attrs || {});
  node.ownerDocument = dom.document;
  (children || []).forEach((child) => {
    node.appendChild(child);
  });
  return node;
}

function loadAdapterHooks(dom) {
  const hooks = {};
  const sandbox = {
    chrome: {
      runtime: {
        sendMessage() {},
        onMessage: { addListener() {} },
        onConnect: { addListener() {} },
        getURL(resource) {
          return resource;
        },
        lastError: null,
      },
    },
    document: dom.document,
    window: dom.window,
    MutationObserver: class {
      observe() {}
      disconnect() {}
    },
    FrameNestCompanion: companion,
    FrameNestXAdapterContractV1: contract,
    FrameNestXAdapterTestHooks: hooks,
  };
  sandbox.globalThis = sandbox;
  vm.runInNewContext(adapterSource, sandbox, { filename: "x_adapter.js" });
  return hooks;
}

function pathDataFrom(node, out) {
  const collected = out || [];
  if (node && node.attrs && node.attrs.d) {
    collected.push(node.attrs.d);
  }
  (node.childNodes || []).forEach((child) => {
    pathDataFrom(child, collected);
  });
  return collected;
}

test("injectAttach does not treat WeakSet membership as a permanent skip", () => {
  const injectFn = adapterSource.match(/function injectAttach\(composerRoot\) \{[\s\S]*?\n  \}/);
  assert.ok(injectFn);
  assert.match(injectFn[0], /injected\.has\(composerRoot\)/);
  assert.match(injectFn[0], /document\.contains/);
  assert.match(injectFn[0], /document\.documentElement\.appendChild\(button\)/);
  assert.doesNotMatch(injectFn[0], /if \(injected\.has\(composerRoot\)\) \{\s*return;/);
  assert.doesNotMatch(injectFn[0], /textRow\.appendChild/);
  assert.doesNotMatch(injectFn[0], /ensureContainingBlock/);
  assert.doesNotMatch(injectFn[0], /markStale/);
  assert.doesNotMatch(adapterSource, /hops < 12/);
  assert.match(adapterSource, /hops < 48/);
  assert.match(adapterSource, /composerChromeHasSignal/);
  assert.match(adapterSource, /composerMediaButtonSelectors/);
});

test("findComposerTextRow uses the non-editable parent when chrome has only the textbox", () => {
  const dom = createMiniDom();
  const editable = el(dom, "div", {
    "data-testid": "tweetTextarea_0",
    contenteditable: "true",
    "aria-label": "Post your reply",
  });
  const toolbar = el(dom, "div", { "data-testid": "toolBar", role: "toolbar" });
  const chrome = el(dom, "div", {}, [editable, toolbar]);
  dom.body.appendChild(chrome);
  const hooks = loadAdapterHooks(dom);
  const foundChrome = hooks.findComposerChrome(editable);
  assert.equal(foundChrome, chrome);
  const row = hooks.findComposerTextRow(editable, foundChrome);
  assert.ok(row);
  assert.equal(row, chrome);
  assert.notEqual(row, editable);
  assert.equal(row.getAttribute("contenteditable"), null);
});

test("findComposerChrome reaches a toolbar ancestor beyond 12 hops", () => {
  const dom = createMiniDom();
  const editable = el(dom, "div", {
    "data-testid": "tweetTextarea_0",
    contenteditable: "true",
    "aria-label": "Post your reply",
  });
  let inner = editable;
  for (let i = 0; i < 20; i += 1) {
    inner = el(dom, "div", {}, [inner]);
  }
  const toolbar = el(dom, "div", { "data-testid": "toolBar", role: "toolbar" });
  const chrome = el(dom, "div", {}, [inner, toolbar]);
  dom.body.appendChild(chrome);
  const hooks = loadAdapterHooks(dom);
  assert.equal(hooks.findComposerChrome(editable), chrome);
  const row = hooks.findComposerTextRow(editable, chrome);
  assert.ok(row);
  assert.notEqual(row, editable);
  assert.equal(row.getAttribute("contenteditable"), null);
});

test("injectAttach re-injects after the attach node leaves the document", () => {
  const dom = createMiniDom();
  const editable = el(dom, "div", {
    "data-testid": "tweetTextarea_0",
    contenteditable: "true",
    "aria-label": "Post your reply",
  });
  const toolbar = el(dom, "div", { "data-testid": "toolBar", role: "toolbar" });
  const file = el(dom, "input", { type: "file", accept: "image/*,video/mp4" });
  const chrome = el(dom, "div", {}, [editable, toolbar, file]);
  dom.body.appendChild(chrome);
  const hooks = loadAdapterHooks(dom);
  hooks.injectAttach(editable);
  const firstButton = dom.document.documentElement.querySelector("[data-framenest-companion='attach']");
  assert.ok(firstButton);
  assert.equal(firstButton.parentElement, dom.document.documentElement);
  assert.equal(chrome.querySelector("[data-framenest-companion='attach']"), null);
  firstButton.parentElement.removeChild(firstButton);
  assert.equal(dom.document.documentElement.querySelector("[data-framenest-companion='attach']"), null);
  assert.equal(dom.document.contains(firstButton), false);
  hooks.injectAttach(editable);
  const secondButton = dom.document.documentElement.querySelector("[data-framenest-companion='attach']");
  assert.ok(secondButton);
  assert.notEqual(secondButton, firstButton);
  assert.equal(secondButton.parentElement, dom.document.documentElement);
});

test("injectAttach does not mount inside the text row or set a host containing block", () => {
  const dom = createMiniDom();
  const editable = el(dom, "div", {
    "data-testid": "tweetTextarea_0",
    contenteditable: "true",
    "aria-label": "Post your reply",
  });
  const row = el(dom, "div", { "data-framenest-composer-text-row": "" }, [editable]);
  const toolbar = el(dom, "div", { "data-testid": "toolBar", role: "toolbar" });
  const file = el(dom, "input", { type: "file", accept: "image/*,video/mp4" });
  const chrome = el(dom, "div", { "data-framenest-composer-chrome": "" }, [row, toolbar, file]);
  dom.body.appendChild(chrome);
  dom.window.getComputedStyle = () => ({ position: "static" });
  const hooks = loadAdapterHooks(dom);
  hooks.injectAttach(editable);
  const button = dom.document.documentElement.querySelector("[data-framenest-companion='attach']");
  assert.ok(button);
  assert.equal(button.parentElement, dom.document.documentElement);
  assert.equal(row.querySelector("[data-framenest-companion='attach']"), null);
  assert.equal(chrome.querySelector("[data-framenest-companion='attach']"), null);
  assert.notEqual(row.style.position, "relative");
  assert.notEqual(chrome.style.position, "relative");
  assert.notEqual(editable.style.position, "relative");
  assert.equal(button.style.position, "fixed");
});

test("missing composer file input skips that composer without page-wide stale", () => {
  const dom = createMiniDom();
  const editable = el(dom, "div", {
    "data-testid": "tweetTextarea_0",
    contenteditable: "true",
    "aria-label": "Post your reply",
  });
  const toolbar = el(dom, "div", { "data-testid": "toolBar", role: "toolbar" });
  const chrome = el(dom, "div", {}, [editable, toolbar]);
  dom.body.appendChild(chrome);
  const hooks = loadAdapterHooks(dom);
  hooks.injectAttach(editable);
  assert.equal(chrome.querySelector("[data-framenest-companion='attach']"), null);
  const save = el(dom, "button", { "data-framenest-companion": "save" });
  dom.body.appendChild(save);
  hooks.injectAttach(editable);
  assert.equal(save.getAttribute("disabled"), null);
});

test("failed Save overlay keeps the plus glyph", () => {
  const dom = createMiniDom();
  const hooks = loadAdapterHooks(dom);
  const failed = hooks.saveIconSvg("failed");
  const idle = hooks.saveIconSvg("idle");
  const paths = pathDataFrom(failed);
  assert.ok(paths.includes("M12 6.5v11M6.5 12h11"));
  assert.equal(paths.some((d) => d.includes("M8 8l8 8") || d.includes("M16 8l-8 8")), false);
  assert.ok(pathDataFrom(idle).includes("M12 6.5v11M6.5 12h11"));
});
