// Movie identification Load/status draft boundary checks for the packaged web shell.

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

function createToggleStub() {
  return {
    hidden: true,
    disabled: true,
    textContent: "",
    attrs: {},
    setAttribute(name, value) {
      this.attrs[name] = String(value);
    },
    getAttribute(name) {
      return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null;
    },
  };
}

function createDurableRenderContext(overrides = {}) {
  const context = {
    metadataWorkspace: { openMediaId: "media-1" },
    metadataDurableAnalysis: {
      mediaId: "media-1",
      state: "analyzed",
      analysisDefinition: "movie_identification",
      detailsExpanded: true,
      movieResult: null,
      result: null,
    },
    metadataAiDetailsToggle: createToggleStub(),
    metadataDurableAiSuggestion: { hidden: true },
    metadataDurableAiTitle: { textContent: "stale-title" },
    metadataDurableAiDescription: { textContent: "stale-description" },
    metadataDurableAiGenres: { textContent: "stale-genres" },
    metadataDurableAiTags: { textContent: "stale-tags" },
    metadataDurableAiCollectionRow: { hidden: true },
    metadataDurableAiCollection: { textContent: "" },
    metadataDurableAiFilenameRow: { hidden: true },
    metadataDurableAiFilename: { textContent: "" },
    movieSuggestionFromResult(result) {
      if (!result) return null;
      return {
        title: result.title || "",
        description: result.description || "",
        genres: Array.isArray(result.genres) ? result.genres : [],
        tags: Array.isArray(result.tags) ? result.tags : [],
        confidence: result.confidence || "",
        suggestedFilename: result.suggestedFilename || "",
      };
    },
    aiSuggestionFromAutomaticAnalysisResult() {
      return null;
    },
    ...overrides,
  };
  vm.createContext(context);
  vm.runInContext(extractFunction("renderMetadataDurableAnalysis"), context);
  return context;
}

test("movie identification helpers preserve Load boundary and taxonomy mapping", () => {
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

test("movie Identify and Load stay non-canonical in source", () => {
  assert.match(APP_SOURCE, /Running movie identification/);
  assert.match(APP_SOURCE, /Loading movie identification/);
  assert.match(APP_SOURCE, /Empty suggestion fields will not clear existing draft values/);
  const start = APP_SOURCE.indexOf('document.querySelector("#metadata-movie-identify-button")');
  assert.ok(start >= 0);
  const identifyBlock = APP_SOURCE.slice(start, APP_SOURCE.indexOf("let commandSearchDebounceTimer"));
  assert.match(identifyBlock, /movie-identification/);
  assert.doesNotMatch(identifyBlock, /handleSaveMetadata/);
  assert.doesNotMatch(identifyBlock, /method:\s*"PUT"/);
  const loadStart = APP_SOURCE.indexOf("async function handleLoadDurableAiSuggestion");
  const loadEnd = APP_SOURCE.indexOf("async function handleAnalyzeMetadataByAi");
  const loadBlock = APP_SOURCE.slice(loadStart, loadEnd);
  assert.match(loadBlock, /movieIdentificationEndpoint/);
  assert.doesNotMatch(loadBlock, /handleSaveMetadata/);
  assert.doesNotMatch(loadBlock, /method:\s*"PUT"/);
});

test("durable movie suggestion markup separates Suggested genres and Suggested tags", () => {
  const detailsBlock = INDEX_SOURCE.slice(
    INDEX_SOURCE.indexOf('id="metadata-durable-ai-suggestion"'),
    INDEX_SOURCE.indexOf('id="metadata-save-button"'),
  );
  assert.match(detailsBlock, /<dt>Suggested genres<\/dt>/);
  assert.match(detailsBlock, /id="metadata-durable-ai-genres"/);
  assert.match(detailsBlock, /<dt>Suggested tags<\/dt>/);
  assert.match(detailsBlock, /id="metadata-durable-ai-tags"/);
  assert.equal((detailsBlock.match(/Suggested tags/g) || []).length, 1);
  assert.equal((detailsBlock.match(/Suggested genres/g) || []).length, 1);
  assert.equal((detailsBlock.match(/id="metadata-durable-ai-genres"/g) || []).length, 1);
  assert.equal((detailsBlock.match(/id="metadata-durable-ai-tags"/g) || []).length, 1);
  assert.doesNotMatch(detailsBlock, /Confidence/i);
  const genresAt = detailsBlock.indexOf('id="metadata-durable-ai-genres"');
  const tagsAt = detailsBlock.indexOf('id="metadata-durable-ai-tags"');
  assert.ok(genresAt >= 0 && tagsAt > genresAt);
});

test("durable renderer does not concatenate genres into tags", () => {
  const durableBody = extractFunction("renderMetadataDurableAnalysis");
  assert.match(durableBody, /metadataDurableAiGenres/);
  assert.match(durableBody, /detailGenres/);
  assert.match(durableBody, /detailTags/);
  assert.doesNotMatch(durableBody, /\.\.\.suggestion\.genres,\s*\.\.\.suggestion\.tags/);
  assert.doesNotMatch(durableBody, /\[\.\.\.suggestion\.genres/);
  assert.match(APP_SOURCE, /#metadata-durable-ai-genres/);
});

test("durable movie suggestion renders overlapping genres and tags as distinct facets", () => {
  const context = createDurableRenderContext();
  context.metadataDurableAnalysis.movieResult = {
    title: "The Tinder Swindler",
    description: "The Tinder Swindler",
    genres: ["Documentary", "Crime"],
    tags: ["Documentary", "Crime"],
    confidence: "high",
  };
  context.renderMetadataDurableAnalysis();

  assert.equal(context.metadataDurableAiSuggestion.hidden, false);
  assert.equal(context.metadataDurableAiTitle.textContent, "The Tinder Swindler");
  assert.equal(context.metadataDurableAiDescription.textContent, "The Tinder Swindler");
  assert.equal(context.metadataDurableAiGenres.textContent, "Documentary, Crime");
  assert.equal(context.metadataDurableAiTags.textContent, "Documentary, Crime");
  assert.notEqual(
    context.metadataDurableAiTags.textContent,
    "Documentary, Crime, Documentary, Crime",
  );
  assert.doesNotMatch(context.metadataDurableAiGenres.textContent, /Documentary, Crime, Documentary/);
  assert.doesNotMatch(context.metadataDurableAiTags.textContent, /Documentary, Crime, Documentary/);
  assert.equal(context.metadataAiDetailsToggle.getAttribute("aria-expanded"), "true");
  assert.equal(
    Object.values(context).some((value) => (
      value
      && typeof value === "object"
      && value.textContent
      && /confidence/i.test(String(value.textContent))
    )),
    false,
  );
});

test("durable movie suggestion keeps distinct genre and tag facet values", () => {
  const context = createDurableRenderContext();
  context.metadataDurableAnalysis.movieResult = {
    title: "Distinct Facets",
    description: "Distinct description",
    genres: ["Documentary"],
    tags: ["Romance scam", "True crime"],
  };
  context.renderMetadataDurableAnalysis();
  assert.equal(context.metadataDurableAiGenres.textContent, "Documentary");
  assert.equal(context.metadataDurableAiTags.textContent, "Romance scam, True crime");
});

test("durable movie suggestion empty and reset semantics clear stale facet values", () => {
  const context = createDurableRenderContext();
  context.metadataDurableAnalysis.movieResult = {
    title: "First",
    description: "First description",
    genres: ["Documentary", "Crime"],
    tags: ["Documentary", "Crime"],
  };
  context.renderMetadataDurableAnalysis();
  assert.equal(context.metadataDurableAiGenres.textContent, "Documentary, Crime");
  assert.equal(context.metadataDurableAiTags.textContent, "Documentary, Crime");

  context.metadataDurableAnalysis.movieResult = {
    title: "Empty genres",
    description: "Has tags",
    genres: [],
    tags: ["Romance scam"],
  };
  context.renderMetadataDurableAnalysis();
  assert.equal(context.metadataDurableAiGenres.textContent, "(none)");
  assert.equal(context.metadataDurableAiTags.textContent, "Romance scam");

  context.metadataDurableAnalysis.movieResult = {
    title: "Empty tags",
    description: "Has genres",
    genres: ["Crime"],
    tags: [],
  };
  context.renderMetadataDurableAnalysis();
  assert.equal(context.metadataDurableAiGenres.textContent, "Crime");
  assert.equal(context.metadataDurableAiTags.textContent, "(none)");

  context.metadataDurableAnalysis.movieResult = {
    title: "Both empty",
    description: "Both empty",
    genres: [],
    tags: [],
  };
  context.renderMetadataDurableAnalysis();
  assert.equal(context.metadataDurableAiGenres.textContent, "(none)");
  assert.equal(context.metadataDurableAiTags.textContent, "(none)");

  context.metadataDurableAnalysis.detailsExpanded = false;
  context.renderMetadataDurableAnalysis();
  assert.equal(context.metadataDurableAiSuggestion.hidden, true);
  assert.equal(context.metadataDurableAiTitle.textContent, "");
  assert.equal(context.metadataDurableAiDescription.textContent, "");
  assert.equal(context.metadataDurableAiGenres.textContent, "");
  assert.equal(context.metadataDurableAiTags.textContent, "");
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
  assert.doesNotMatch(extractFunction("renderMetadataDurableAnalysis"), /handleSaveMetadata/);
  assert.doesNotMatch(extractFunction("renderMetadataDurableAnalysis"), /method:\s*"PUT"/);
});
