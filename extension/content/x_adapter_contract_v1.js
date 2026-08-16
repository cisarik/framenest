(function (root) {
  const contract = Object.freeze({
    adapterVersion: 1,
    postRoots: Object.freeze(["article[data-testid='tweet']", "[data-framenest-post]"]),
    permalinkSelectors: Object.freeze([
      "a[href*='/status/'][role='link']",
      "a[href*='/status/'] time",
      "a[href*='/status/']",
    ]),
    composerRoots: Object.freeze([
      "[data-testid='tweetTextarea_0']",
      "[data-framenest-composer]",
    ]),
    composerFileInputs: Object.freeze([
      "input[data-framenest-composer-file]",
      "input[type='file'][accept*='image']",
      "input[type='file']",
    ]),
    composerToolbarSelectors: Object.freeze([
      "[data-testid='toolBar']",
      "[data-framenest-composer-toolbar]",
    ]),
    bookmarkSelectors: Object.freeze([
      "[data-testid='bookmark']",
      "[data-testid='removeBookmark']",
      "[aria-label='Bookmark']",
      "[aria-label='Add to Bookmarks']",
    ]),
    actionGroupSelectors: Object.freeze(["[role='group']"]),
    actionBarSignals: Object.freeze([
      "[data-testid='reply']",
      "[data-testid='retweet']",
      "[data-testid='like']",
    ]),
    shareSelectors: Object.freeze([
      "[data-testid='share']",
      "[aria-label='Share post']",
      "[aria-label='Share']",
    ]),
    requiredSignals: Object.freeze(["permalink", "composerFileInput"]),
  });
  if (typeof module !== "undefined" && module.exports) {
    module.exports = contract;
  }
  root.FrameNestXAdapterContractV1 = contract;
})(typeof globalThis !== "undefined" ? globalThis : this);
