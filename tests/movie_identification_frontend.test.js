// Movie identification status/draft boundary checks for the packaged web shell.

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const APP_SOURCE = fs.readFileSync(
  path.join(__dirname, "..", "src", "framenest", "adapters", "api", "web", "app.js"),
  "utf8",
);
const INDEX_SOURCE = fs.readFileSync(
  path.join(__dirname, "..", "src", "framenest", "adapters", "api", "web", "index.html"),
  "utf8",
);

function extractFunction(name) {
  const start = APP_SOURCE.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `missing function ${name}`);
  let depth = 0;
  let started = false;
  for (let index = start; index < APP_SOURCE.length; index += 1) {
    const char = APP_SOURCE[index];
    if (char === "{") {
      depth += 1;
      started = true;
    } else if (char === "}") {
      depth -= 1;
      if (started && depth === 0) {
        return APP_SOURCE.slice(start, index + 1);
      }
    }
  }
  throw new Error(`failed to extract ${name}`);
}

function extractConstArray(name) {
  const match = APP_SOURCE.match(new RegExp(`const ${name} = \\[([\\s\\S]*?)\\];`));
  assert.ok(match, `missing const ${name}`);
  return `const ${name} = [${match[1]}];`;
}

function createStripElement() {
  return {
    hidden: true,
    className: "",
    textContent: "",
    attrs: {},
    children: [],
    classList: {
      toggle() {},
    },
    setAttribute(name, value) {
      this.attrs[name] = String(value);
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null;
    },
    addEventListener() {},
    replaceChildren(...nodes) {
      this.children = [...nodes];
    },
    appendChild(node) {
      this.children.push(node);
      return node;
    },
  };
}

function stripValueText(strip) {
  return strip.children
    .filter((child) => child.className !== "metadata-suggestion-strip__apply")
    .map((child) => child.textContent)
    .join("");
}

function stripChipValues(strip) {
  return strip.children.map((child) => child.textContent);
}

function collectStripRenderText(context) {
  return [
    context.metadataAiTitleStrip,
    context.metadataAiDescriptionStrip,
    context.metadataAiTagsStrip,
  ]
    .flatMap((strip) => [strip.textContent, ...strip.children.map((child) => child.textContent)])
    .join("\n");
}

function createStripRenderContext() {
  const context = {
    metadataSuggestionList: {
      mediaId: "media-1",
      fetching: false,
      items: [],
      selectedRunId: null,
      errorMessage: "",
      movieExcluded: false,
    },
    metadataAiTitleStrip: createStripElement(),
    metadataAiDescriptionStrip: createStripElement(),
    metadataAiTagsStrip: createStripElement(),
    identityAllowsAiSuggestionChrome() {
      return true;
    },
    metadataWorkspace: { current: { tagKeys: [] } },
    metadataWorkspaceIsAliasMode() {
      return false;
    },
    copySuggestionFieldToCurrent() {},
    document: {
      createElement() {
        return createStripElement();
      },
    },
  };
  vm.createContext(context);
  vm.runInContext(extractConstArray("MOVIE_GENRE_OPTIONS"), context);
  vm.runInContext(extractFunction("movieIdentificationIsPureUnknown"), context);
  vm.runInContext(extractFunction("movieIdentificationHasLoadableFields"), context);
  vm.runInContext(extractFunction("movieSuggestionFromResult"), context);
  vm.runInContext(extractFunction("selectedMetadataSuggestion"), context);
  vm.runInContext(extractFunction("clearMetadataSuggestionStrip"), context);
  vm.runInContext(extractFunction("appendSuggestionApplyButton"), context);
  vm.runInContext(extractFunction("renderMetadataSuggestionStrips"), context);
  return context;
}

test("movie identification helpers preserve draft boundary and taxonomy mapping", () => {
  assert.match(APP_SOURCE, /function movieIdentificationEndpoint/);
  assert.match(APP_SOURCE, /function applyMovieIdentificationToMetadataWorkspace/);
  assert.match(APP_SOURCE, /function movieIdentificationIsPureUnknown/);
  assert.match(APP_SOURCE, /function movieIdentificationHasLoadableFields/);
  assert.match(APP_SOURCE, /movieIdentificationEndpoint\(mediaId\)/);
  assert.match(APP_SOURCE, /applyMovieIdentificationToMetadataWorkspace\(movieResult, tagKeys\)/);

  const context = {
    MOVIE_GENRE_OPTIONS: undefined,
    metadataWorkspace: {
      current: {
        displayTitle: "Keep Me",
        description: "Keep description",
        tagKeys: ["keep-tag"],
        genres: ["Drama"],
      },
      suggestedFilename: null,
      aiSuggestionApplied: false,
      statusOverride: null,
    },
    metadataAiStatus: { textContent: "" },
    advanceMetadataWorkspaceRevision() {},
  };
  vm.createContext(context);
  vm.runInContext(extractConstArray("MOVIE_GENRE_OPTIONS"), context);
  vm.runInContext(extractFunction("movieIdentificationIsPureUnknown"), context);
  vm.runInContext(extractFunction("movieIdentificationHasLoadableFields"), context);
  vm.runInContext(extractFunction("movieSuggestionFromResult"), context);
  vm.runInContext(extractFunction("applyMovieIdentificationToMetadataWorkspace"), context);

  const unknown = {
    identified_title: null,
    identification_status: "unknown",
    confidence: "unknown",
    genres: [],
    tags: [],
    description: "Movie could not be identified from the available frames.",
  };
  assert.equal(context.movieIdentificationIsPureUnknown(unknown), true);
  assert.equal(context.movieIdentificationHasLoadableFields(unknown), false);
  assert.equal(context.movieSuggestionFromResult(unknown), null);

  const identified = {
    identified_title: "Synthetic Adventure",
    identification_status: "identified",
    confidence: "high",
    genres: ["Adventure", "not-a-genre"],
    tags: ["desert"],
    description: "A synthetic adventure film.",
  };
  assert.equal(context.movieIdentificationHasLoadableFields(identified), true);
  const mapped = context.movieSuggestionFromResult(identified);
  assert.equal(mapped.title, "Synthetic Adventure");
  assert.deepEqual(mapped.genres, ["Adventure"]);
  assert.deepEqual(mapped.tags, ["desert"]);
  assert.equal(mapped.confidence, "high");

  context.applyMovieIdentificationToMetadataWorkspace(identified, ["desert"]);
  assert.equal(context.metadataWorkspace.current.displayTitle, "Synthetic Adventure");
  assert.equal(context.metadataWorkspace.current.description, "A synthetic adventure film.");
  assert.deepEqual(context.metadataWorkspace.current.genres, ["Adventure"]);
  assert.deepEqual(context.metadataWorkspace.current.tagKeys, ["desert"]);

  // Empty fields must not erase existing draft values.
  context.applyMovieIdentificationToMetadataWorkspace(
    {
      identified_title: null,
      description: "",
      genres: [],
      tags: [],
      identification_status: "ambiguous",
    },
    [],
  );
  assert.equal(context.metadataWorkspace.current.displayTitle, "Synthetic Adventure");
  assert.equal(context.metadataWorkspace.current.description, "A synthetic adventure film.");
  assert.deepEqual(context.metadataWorkspace.current.genres, ["Adventure"]);
  assert.deepEqual(context.metadataWorkspace.current.tagKeys, ["desert"]);
});

test("movie Identify and suggestion review stay non-canonical in source", () => {
  assert.match(APP_SOURCE, /Running movie identification/);
  assert.match(APP_SOURCE, /Movie identification in progress\./);
  // Empty suggestion fields must not clear existing draft values.
  const applyBody = extractFunction("applyMovieIdentificationToMetadataWorkspace");
  assert.match(applyBody, /if \(title\) \{/);
  assert.match(applyBody, /if \(description\) \{/);
  assert.match(applyBody, /if \(genres\.length > 0\) \{/);
  assert.match(applyBody, /if \(Array\.isArray\(tagKeys\) && tagKeys\.length > 0\) \{/);
  const start = APP_SOURCE.indexOf('document.querySelector("#metadata-movie-identify-button")');
  assert.ok(start >= 0);
  const identifyBlock = APP_SOURCE.slice(start, APP_SOURCE.indexOf("let commandSearchDebounceTimer"));
  assert.match(identifyBlock, /movie-identification/);
  assert.doesNotMatch(identifyBlock, /handleSaveMetadata/);
  assert.doesNotMatch(identifyBlock, /method:\s*"PUT"/);
  assert.equal(APP_SOURCE.includes("handleLoadDurableAiSuggestion"), false);
  // Movie identification status fetch stays on the read-only status surface.
  const statusStart = APP_SOURCE.indexOf("async function refreshMetadataDurableAnalysis");
  const statusEnd = APP_SOURCE.indexOf("function applyAnalysisStatusPayload");
  assert.ok(statusStart >= 0 && statusEnd > statusStart);
  const statusBlock = APP_SOURCE.slice(statusStart, statusEnd);
  assert.match(statusBlock, /movieIdentificationEndpoint/);
  assert.doesNotMatch(statusBlock, /handleSaveMetadata/);
  assert.doesNotMatch(statusBlock, /method:\s*"PUT"/);
});

test("durable movie suggestion markup separates Suggested genres and Suggested tags", () => {
  const workspaceBlock = INDEX_SOURCE.slice(
    INDEX_SOURCE.indexOf('id="metadata-ai-title-strip"'),
    INDEX_SOURCE.indexOf('id="metadata-save-button"'),
  );
  assert.match(workspaceBlock, /id="metadata-ai-title-strip"/);
  assert.match(workspaceBlock, /id="metadata-ai-description-strip"/);
  assert.match(workspaceBlock, /id="metadata-ai-tags-strip"/);
  assert.equal((workspaceBlock.match(/id="metadata-ai-title-strip"/g) || []).length, 1);
  assert.equal((workspaceBlock.match(/id="metadata-ai-description-strip"/g) || []).length, 1);
  assert.equal((workspaceBlock.match(/id="metadata-ai-tags-strip"/g) || []).length, 1);
  // Genres stay a separate draft-side facet surface (the movie genre fieldset),
  // never merged into the suggestion tag strip.
  assert.match(workspaceBlock, /id="metadata-genres-fieldset"/);
  assert.equal((workspaceBlock.match(/id="metadata-genres-fieldset"/g) || []).length, 1);
  assert.equal((workspaceBlock.match(/metadata-suggestion-strip--tags/g) || []).length, 1);
  assert.doesNotMatch(workspaceBlock, /Confidence/i);
  const genresAt = workspaceBlock.indexOf('id="metadata-genres-fieldset"');
  const tagsAt = workspaceBlock.indexOf('id="metadata-ai-tags-strip"');
  assert.ok(genresAt >= 0 && tagsAt > genresAt);
});

test("durable renderer does not concatenate genres into tags", () => {
  const stripsBody = extractFunction("renderMetadataSuggestionStrips");
  assert.match(stripsBody, /metadataAiTagsStrip/);
  assert.match(stripsBody, /item\.tags/);
  assert.doesNotMatch(stripsBody, /\.\.\.suggestion\.genres,\s*\.\.\.suggestion\.tags/);
  assert.doesNotMatch(stripsBody, /\[\.\.\.suggestion\.genres/);
  // The suggestion tag renderer never touches the genre facet at all.
  assert.doesNotMatch(stripsBody, /genres/);
  assert.match(APP_SOURCE, /#metadata-ai-tags-strip/);
});

test("durable movie suggestion renders overlapping genres and tags as distinct facets", () => {
  const context = createStripRenderContext();
  context.metadataSuggestionList.items = [{
    analysisRunId: "run-1",
    title: "The Tinder Swindler",
    description: "The Tinder Swindler",
    tags: [
      { value: "Documentary", status: "mapped", key: "documentary", displayName: "Documentary" },
      { value: "Crime", status: "mapped", key: "crime", displayName: "Crime" },
    ],
  }];
  context.metadataSuggestionList.selectedRunId = "run-1";
  context.renderMetadataSuggestionStrips();

  assert.equal(context.metadataAiTitleStrip.hidden, false);
  assert.equal(context.metadataAiDescriptionStrip.hidden, false);
  assert.equal(context.metadataAiTagsStrip.hidden, false);
  assert.equal(stripValueText(context.metadataAiTitleStrip), "The Tinder Swindler");
  assert.equal(stripValueText(context.metadataAiDescriptionStrip), "The Tinder Swindler");
  assert.deepEqual(stripChipValues(context.metadataAiTagsStrip), ["Documentary", "Crime"]);
  assert.notEqual(
    stripChipValues(context.metadataAiTagsStrip).join(", "),
    "Documentary, Crime, Documentary, Crime",
  );
  assert.doesNotMatch(collectStripRenderText(context), /Documentary, Crime, Documentary/);

  // The movie mapping keeps overlapping genre and tag values as separate facet arrays.
  const mapped = context.movieSuggestionFromResult({
    identified_title: "The Tinder Swindler",
    identification_status: "identified",
    confidence: "high",
    genres: ["Documentary", "Crime"],
    tags: ["Documentary", "Crime"],
    description: "The Tinder Swindler",
  });
  assert.deepEqual(mapped.genres, ["Documentary", "Crime"]);
  assert.deepEqual(mapped.tags, ["Documentary", "Crime"]);
  assert.doesNotMatch(collectStripRenderText(context), /confidence/i);
});

test("durable movie suggestion keeps distinct genre and tag facet values", () => {
  const context = createStripRenderContext();
  // The mapping keeps the genre facet and the tag facet values separate.
  const mapped = context.movieSuggestionFromResult({
    identified_title: "Distinct Facets",
    identification_status: "identified",
    confidence: "high",
    genres: ["Documentary"],
    tags: ["Romance scam", "True crime"],
    description: "Distinct description",
  });
  assert.deepEqual(mapped.genres, ["Documentary"]);
  assert.deepEqual(mapped.tags, ["Romance scam", "True crime"]);

  // The tag facet renders each suggested tag value once, as its own chip.
  context.metadataSuggestionList.items = [{
    analysisRunId: "run-1",
    title: "Distinct Facets",
    description: "Distinct description",
    tags: [
      { value: "Romance scam", status: "mapped", key: "romance-scam", displayName: "Romance scam" },
      { value: "True crime", status: "mapped", key: "true-crime", displayName: "True crime" },
    ],
  }];
  context.metadataSuggestionList.selectedRunId = "run-1";
  context.renderMetadataSuggestionStrips();
  assert.deepEqual(stripChipValues(context.metadataAiTagsStrip), ["Romance scam", "True crime"]);
  assert.equal(stripValueText(context.metadataAiTitleStrip), "Distinct Facets");
  assert.equal(stripValueText(context.metadataAiDescriptionStrip), "Distinct description");
});

test("durable movie suggestion empty and reset semantics clear stale facet values", () => {
  const context = createStripRenderContext();
  context.metadataSuggestionList.items = [{
    analysisRunId: "run-1",
    title: "First",
    description: "First description",
    tags: [
      { value: "Documentary", status: "mapped", key: "documentary", displayName: "Documentary" },
      { value: "Crime", status: "mapped", key: "crime", displayName: "Crime" },
    ],
  }];
  context.metadataSuggestionList.selectedRunId = "run-1";
  context.renderMetadataSuggestionStrips();
  assert.equal(stripValueText(context.metadataAiTitleStrip), "First");
  assert.deepEqual(stripChipValues(context.metadataAiTagsStrip), ["Documentary", "Crime"]);

  // A replacement suggestion with fewer tag values clears the stale chips.
  context.metadataSuggestionList.items = [{
    analysisRunId: "run-1",
    title: "Has tags",
    description: "Has tags",
    tags: [
      { value: "Romance scam", status: "mapped", key: "romance-scam", displayName: "Romance scam" },
    ],
  }];
  context.renderMetadataSuggestionStrips();
  assert.deepEqual(stripChipValues(context.metadataAiTagsStrip), ["Romance scam"]);

  // An empty tag facet hides the strip and leaves no stale chip values.
  context.metadataSuggestionList.items = [{
    analysisRunId: "run-1",
    title: "Empty tags",
    description: "Has genres",
    tags: [],
  }];
  context.renderMetadataSuggestionStrips();
  assert.equal(context.metadataAiTagsStrip.hidden, true);
  assert.equal(context.metadataAiTagsStrip.children.length, 0);

  // Empty text values render deterministic placeholders instead of stale text.
  context.metadataSuggestionList.items = [{
    analysisRunId: "run-1",
    title: "",
    description: "",
    tags: [],
  }];
  context.renderMetadataSuggestionStrips();
  assert.equal(stripValueText(context.metadataAiTitleStrip), "(No title)");
  assert.equal(stripValueText(context.metadataAiDescriptionStrip), "(No description)");
  assert.equal(context.metadataAiTagsStrip.hidden, true);
  assert.equal(context.metadataAiTagsStrip.children.length, 0);

  // Reset (no selected suggestion) hides every strip and clears stale values.
  context.metadataSuggestionList.selectedRunId = null;
  context.renderMetadataSuggestionStrips();
  for (const strip of [
    context.metadataAiTitleStrip,
    context.metadataAiDescriptionStrip,
    context.metadataAiTagsStrip,
  ]) {
    assert.equal(strip.hidden, true);
    assert.equal(strip.children.length, 0);
  }
});

test("movie suggestion mapping preserves separate genres tags and confidence without Save", () => {
  const context = {
    MOVIE_GENRE_OPTIONS: undefined,
  };
  vm.createContext(context);
  vm.runInContext(extractConstArray("MOVIE_GENRE_OPTIONS"), context);
  vm.runInContext(extractFunction("movieIdentificationIsPureUnknown"), context);
  vm.runInContext(extractFunction("movieIdentificationHasLoadableFields"), context);
  vm.runInContext(extractFunction("movieSuggestionFromResult"), context);

  const mapped = context.movieSuggestionFromResult({
    identified_title: "The Tinder Swindler",
    identification_status: "identified",
    confidence: "high",
    genres: ["Documentary", "Crime"],
    tags: ["Documentary", "Crime"],
    description: "The Tinder Swindler",
  });
  assert.deepEqual(mapped.genres, ["Documentary", "Crime"]);
  assert.deepEqual(mapped.tags, ["Documentary", "Crime"]);
  assert.equal(mapped.confidence, "high");
  assert.equal(mapped.title, "The Tinder Swindler");
  assert.equal(mapped.description, "The Tinder Swindler");

  const applyBody = extractFunction("applyMovieIdentificationToMetadataWorkspace");
  assert.match(applyBody, /metadataWorkspace\.current\.genres = genres/);
  assert.match(applyBody, /metadataWorkspace\.current\.tagKeys = tagKeys/);
  assert.doesNotMatch(applyBody, /handleSaveMetadata/);
  assert.doesNotMatch(applyBody, /method:\s*"PUT"/);
  assert.doesNotMatch(extractFunction("renderMetadataSuggestionStrips"), /handleSaveMetadata/);
  assert.doesNotMatch(extractFunction("renderMetadataSuggestionStrips"), /method:\s*"PUT"/);
});
