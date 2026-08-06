const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const APP_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../src/framenest/adapters/api/web/app.js"),
  "utf8",
);
const INDEX_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../src/framenest/adapters/api/web/index.html"),
  "utf8",
);
const STYLES_SOURCE = fs.readFileSync(
  path.resolve(__dirname, "../src/framenest/adapters/api/web/styles.css"),
  "utf8",
);

test("ordinary My YouTube downloads is capability-gated and sanitized", () => {
  assert.match(APP_SOURCE, /identityAllowsYouTubeRequest/);
  assert.match(APP_SOURCE, /capabilities\.has\("youtube\.request"\)/);
  assert.match(APP_SOURCE, /YOUTUBE_REQUESTS_ENDPOINT\s*=\s*"\/api\/youtube\/requests"/);
  assert.match(INDEX_SOURCE, /id="youtube-request-open-button"/);
  assert.match(INDEX_SOURCE, /My YouTube downloads/);
  assert.match(INDEX_SOURCE, /id="youtube-request-dialog"/);
  assert.match(INDEX_SOURCE, /aria-live="polite"/);
  assert.match(APP_SOURCE, /Private until an administrator publishes it/);
  assert.match(APP_SOURCE, /phase === "failed"/);
  assert.doesNotMatch(APP_SOURCE, /youtube\.request[\s\S]{0,200}analysis\.run/);
  assert.doesNotMatch(INDEX_SOURCE, /id="youtube-request-publish"/);
  assert.doesNotMatch(INDEX_SOURCE, /id="youtube-request-ai"/);
  assert.match(STYLES_SOURCE, /\.youtube-request-list/);
  assert.match(STYLES_SOURCE, /min-height:\s*2\.75rem/);
});

test("administrator claim cockpit exposes requester login key only", () => {
  assert.match(INDEX_SOURCE, /id="youtube-claim-requester"/);
  assert.match(APP_SOURCE, /Requested by \$\{key\}/);
  assert.match(APP_SOURCE, /Administrator claim/);
  assert.doesNotMatch(APP_SOURCE, /requester_display_name/);
});
