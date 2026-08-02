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
