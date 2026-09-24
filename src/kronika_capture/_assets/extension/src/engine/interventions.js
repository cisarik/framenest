(() => {
  const root = (globalThis.ChatGPTCLI = globalThis.ChatGPTCLI || {});
  if (root.interventions) return;

  function composerPresent(pack, adapter) {
    const locator = pack && pack.locators ? pack.locators.composer : null;
    if (!locator || !Array.isArray(locator.strategies)) return false;
    for (const strategy of locator.strategies) {
      if (strategy.kind === "url_path") continue;
      if (adapter.queryVisible(strategy).length > 0) return true;
    }
    return false;
  }

  function loginWallDetected(pack, adapter) {
    const locator = pack && pack.locators ? pack.locators.login_wall : null;
    if (!locator || !Array.isArray(locator.strategies)) return false;
    for (const strategy of locator.strategies) {
      if (strategy.kind === "url_path") {
        if (adapter.urlPathMatches(strategy.value)) return true;
        continue;
      }
      if (adapter.queryVisible(strategy).length > 0) return true;
    }
    return false;
  }

  function classify(ctx) {
    const adapter = root.adapter;
    if (!adapter) return null;
    const pack = (ctx && ctx.pack) || {};
    // Blocking dialogs/challenges take precedence even if a composer is visible.
    if (typeof document !== "undefined") {
      const visible = (selector) => [...document.querySelectorAll(selector)].slice(0, 16)
        .filter((node) => node.isConnected && node.getClientRects().length > 0);
      if (visible('iframe[src*="challenges.cloudflare.com"], [name="cf-turnstile-response"]').length)
        return { kind: "captcha" };
      const notices = visible('[role="alert"], [role="dialog"]')
        .map((node) => String(node.textContent || "").slice(0, 512)).join(" ");
      if (/limit reached|usage limit|try again later/i.test(notices)) return { kind: "limit" };
      if (/consent|accept.*(terms|cookies)/i.test(notices)) return { kind: "consent" };
    }
    if (loginWallDetected(pack, adapter)) return { kind: "login" };
    if (composerPresent(pack, adapter)) return null;
    return null;
  }

  root.interventions = { classify, composerPresent, loginWallDetected };
})();
