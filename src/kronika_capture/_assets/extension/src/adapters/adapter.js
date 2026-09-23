(() => {
  const root = (globalThis.ChatGPTCLI = globalThis.ChatGPTCLI || {});
  if (root.adapter) return;

  function attributeValue(value) {
    return JSON.stringify(String(value));
  }

  function normalizeText(value) {
    return String(value == null ? "" : value)
      .replace(/\s+/g, " ")
      .trim()
      .toLowerCase();
  }

  function clickableAncestor(element, scope) {
    const searchRoot = scope || document;
    let node = element;
    while (node && node.nodeType === 1) {
      const tag = node.tagName ? node.tagName.toLowerCase() : "";
      if (
        tag === "button" ||
        node.hasAttribute("role") ||
        node.hasAttribute("tabindex")
      ) {
        return node;
      }
      if (node === searchRoot || node === document.documentElement) break;
      node = node.parentElement;
    }
    return element;
  }

  function queryText(strategy, scope) {
    const searchRoot = scope || document;
    const expected = normalizeText(strategy.value);
    if (!expected) return [];
    const exact = strategy.exact !== false;
    let candidates;
    try {
      candidates = Array.from(
        searchRoot.querySelectorAll("button, a, [role], div, span")
      );
    } catch (error) {
      return [];
    }
    const matches = [];
    for (const element of candidates) {
      if (!isVisible(element)) continue;
      const text = normalizeText(element.textContent);
      if (!text) continue;
      const matched = exact ? text === expected : text.includes(expected);
      if (!matched) continue;
      const target = clickableAncestor(element, searchRoot);
      if (!matches.includes(target)) matches.push(target);
    }
    return matches;
  }

  function query(strategy, scope) {
    const searchRoot = scope || document;
    if (!strategy || typeof strategy.kind !== "string") return [];
    switch (strategy.kind) {
      case "css":
        try {
          return Array.from(searchRoot.querySelectorAll(strategy.value));
        } catch (error) {
          return [];
        }
      case "testid":
        try {
          return Array.from(
            searchRoot.querySelectorAll(
              "[data-testid=" + attributeValue(strategy.value) + "]"
            )
          );
        } catch (error) {
          return [];
        }
      case "role": {
        let elements;
        try {
          elements = Array.from(
            searchRoot.querySelectorAll('[role=' + attributeValue(strategy.value) + "]")
          );
        } catch (error) {
          return [];
        }
        if (!strategy.name) return elements;
        const expected = String(strategy.name);
        return elements.filter((element) => {
          const label =
            element.getAttribute("aria-label") ||
            element.getAttribute("placeholder") ||
            (element.textContent || "").trim();
          return strategy.exact ? label === expected : label.includes(expected);
        });
      }
      case "url_path":
        return [];
      case "text":
        return queryText(strategy, searchRoot);
      default:
        return [];
    }
  }

  function isVisible(element) {
    if (!element || element.nodeType !== 1 || !element.isConnected) return false;
    const style = window.getComputedStyle(element);
    if (!style || style.display === "none") return false;
    if (style.visibility === "hidden" || style.visibility === "collapse") return false;
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }

  function queryVisible(strategy, scope) {
    return query(strategy, scope).filter(isVisible);
  }

  function urlPathMatches(value) {
    return window.location.pathname.includes(String(value));
  }

  function probe(pack) {
    const results = [];
    const locators = pack && pack.locators ? pack.locators : {};
    for (const key of Object.keys(locators)) {
      const locator = locators[key];
      let found = false;
      for (const strategy of locator.strategies || []) {
        if (strategy.kind === "url_path") {
          if (urlPathMatches(strategy.value)) {
            found = true;
            break;
          }
          continue;
        }
        if (queryVisible(strategy).length > 0) {
          found = true;
          break;
        }
      }
      results.push({
        probe: key,
        status: found ? "pass" : locator.required ? "fail" : "skip",
        detail: "",
      });
    }
    return results;
  }

  root.adapter = {
    query,
    queryVisible,
    isVisible,
    urlPathMatches,
    probe,
  };
})();
