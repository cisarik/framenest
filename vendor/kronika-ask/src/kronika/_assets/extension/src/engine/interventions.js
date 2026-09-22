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
    if (composerPresent(pack, adapter)) return null;
    if (loginWallDetected(pack, adapter)) return { kind: "login" };
    return null;
  }

  root.interventions = { classify, composerPresent, loginWallDetected };
})();
