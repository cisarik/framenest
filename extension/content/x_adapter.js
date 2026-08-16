(function () {
  const companion = globalThis.FrameNestCompanion;
  const contract = globalThis.FrameNestXAdapterContractV1;
  if (!companion || !contract) {
    return;
  }

  const injected = new WeakSet();
  const inflightByClaim = new Map();
  let stale = false;
  let boundComposer = null;

  function first(root, selectors) {
    for (const selector of selectors) {
      const node = root.querySelector(selector);
      if (node) {
        return node;
      }
    }
    return null;
  }

  function permalinkFrom(postRoot) {
    for (const selector of contract.permalinkSelectors) {
      const node = postRoot.querySelector(selector);
      if (!node) {
        continue;
      }
      const href = node.getAttribute("href") || (node.closest && node.closest("a") && node.closest("a").getAttribute("href"));
      if (!href) {
        continue;
      }
      const absolute = href.startsWith("http") ? href : "https://x.com" + href.split("?")[0];
      const accepted = companion.acceptXPostUrl(absolute.split("?")[0].split("#")[0]);
      if (accepted) {
        return accepted;
      }
    }
    return null;
  }

  function markStale(reason) {
    stale = true;
    document.querySelectorAll("[data-framenest-companion]").forEach((node) => {
      node.textContent = "FrameNest unavailable";
      node.setAttribute("disabled", "true");
    });
    void reason;
  }

  function send(type, payload) {
    return chrome.runtime.sendMessage(
      { v: companion.PROTOCOL, type, payload: payload || {} },
      function () {
        return undefined;
      }
    );
  }

  function request(type, payload) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage(
        { v: companion.PROTOCOL, type, payload: payload || {} },
        (response) => {
          if (chrome.runtime.lastError) {
            resolve({ ok: false, error: "extension_unavailable" });
            return;
          }
          resolve(response || { ok: false, error: "empty_response" });
        }
      );
    });
  }

  function addButton(parent, label, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-framenest-companion", label);
    button.textContent = label;
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      onClick(button);
    });
    parent.appendChild(button);
    return button;
  }

  function injectSave(postRoot) {
    if (injected.has(postRoot)) {
      return;
    }
    const accepted = permalinkFrom(postRoot);
    if (!accepted) {
      markStale("missing_permalink");
      return;
    }
    injected.add(postRoot);
    addButton(postRoot, "Save to FrameNest", async (button) => {
      if (stale) {
        return;
      }
      button.textContent = "Saving…";
      const result = await request(companion.TYPES.SAVE_POST, {
        url: accepted.submittedUrl,
      });
      if (!result.ok) {
        button.textContent = result.error || "Save failed";
        return;
      }
      button.textContent = result.state || "Submitted";
      if (result.claimId) {
        inflightByClaim.set(result.claimId, button);
        pollClaim(result.claimId);
      }
    });
  }

  function injectAttach(composerRoot) {
    if (injected.has(composerRoot)) {
      return;
    }
    const fileInput = first(composerRoot, contract.composerFileInputs) ||
      first(document, contract.composerFileInputs);
    if (!fileInput) {
      markStale("missing_composer_file_input");
      return;
    }
    injected.add(composerRoot);
    addButton(composerRoot, "Attach from FrameNest", async () => {
      if (stale) {
        return;
      }
      boundComposer = { root: composerRoot, fileInput };
      await request(companion.TYPES.ACK, { composerBound: true });
      chrome.runtime.sendMessage({
        v: companion.PROTOCOL,
        type: companion.TYPES.ACK,
        payload: { openPicker: true },
      });
    });
  }

  async function pollClaim(claimId) {
    const button = inflightByClaim.get(claimId);
    if (!button || !document.contains(button)) {
      return;
    }
    const result = await request(companion.TYPES.POLL_CLAIM, { claimId });
    if (!result.ok) {
      button.textContent = result.error || "Save failed";
      return;
    }
    button.textContent = result.state || "Working…";
    if (result.terminal) {
      inflightByClaim.delete(claimId);
      return;
    }
    window.setTimeout(() => {
      pollClaim(claimId);
    }, 1500);
  }

  async function recover() {
    const result = await request(companion.TYPES.RECOVER_INFLIGHT, {});
    if (!result.ok || !Array.isArray(result.claimIds)) {
      return;
    }
    result.claimIds.forEach((claimId) => {
      pollClaim(claimId);
    });
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    const parsed = companion.dropUnknown(message);
    if (!parsed) {
      return false;
    }
    if (parsed.type === companion.TYPES.ATTACH_BEGIN) {
      attachSelected(parsed.payload || {}).then((result) => sendResponse(result));
      return true;
    }
    return false;
  });

  chrome.runtime.onConnect.addListener((port) => {
    if (!port || port.name !== "framenest-attach") {
      return;
    }
    const chunks = [];
    let total = 0;
    let mediaType = "application/octet-stream";
    let filename = "framenest-media.bin";
    port.onMessage.addListener((message) => {
      const parsed = companion.dropUnknown(message);
      if (!parsed) {
        return;
      }
      if (parsed.payload && parsed.payload.phase === "meta") {
        mediaType = parsed.payload.mediaType || mediaType;
        filename = parsed.payload.filename || filename;
        return;
      }
      if (parsed.payload && parsed.payload.chunk) {
        const bytes = companion.bytesFromBase64(parsed.payload.chunk);
        total += bytes.byteLength;
        if (total > companion.MAX_ATTACH_BYTES) {
          port.postMessage({
            v: companion.PROTOCOL,
            type: companion.TYPES.ERROR,
            payload: { error: "too_large" },
          });
          port.disconnect();
          return;
        }
        chunks.push(bytes);
        return;
      }
      if (parsed.payload && parsed.payload.phase === "end") {
        const fileInput = boundComposer && boundComposer.fileInput;
        if (!fileInput) {
          port.postMessage({
            v: companion.PROTOCOL,
            type: companion.TYPES.ERROR,
            payload: { error: "composer_unbound" },
          });
          return;
        }
        const bytes = companion.concatChunks(chunks, total);
        const file = new File([bytes], filename, { type: mediaType });
        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
        fileInput.dispatchEvent(new Event("change", { bubbles: true }));
        port.postMessage({
          v: companion.PROTOCOL,
          type: companion.TYPES.ACK,
          payload: { attached: true, bytes: total },
        });
      }
    });
  });

  async function attachSelected() {
    return { ok: Boolean(boundComposer && boundComposer.fileInput) };
  }

  function scan() {
    if (stale) {
      return;
    }
    const posts = document.querySelectorAll(contract.postRoots.join(","));
    posts.forEach((post) => injectSave(post));
    const composers = document.querySelectorAll(contract.composerRoots.join(","));
    composers.forEach((composer) => injectAttach(composer));
  }

  const observer = new MutationObserver(() => scan());
  observer.observe(document.documentElement, { childList: true, subtree: true });
  scan();
  recover();
})();
