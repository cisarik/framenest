(() => {
  const root = (globalThis.ChatGPTCLI = globalThis.ChatGPTCLI || {});
  if (root.createEngine) return;

  function createEngine(ctx) {
    if (!root.domEngine || typeof root.domEngine.createDomEngine !== "function") {
      throw new Error("ChatGPTCLI.domEngine is not loaded");
    }
    return root.domEngine.createDomEngine(ctx);
  }

  root.createEngine = createEngine;
  root.ENGINE_VERSION = "0.1.0";
})();
