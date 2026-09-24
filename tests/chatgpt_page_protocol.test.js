import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { unsupportedJob } from "../src/kronika_capture/_assets/extension/src/headless/job_engine.mjs";
import { PROTO_VERSION, ERROR_CODES, CLIENT_CAPABILITIES } from "../src/kronika_capture/_assets/extension/src/protocol.js";

const pack = JSON.parse(
  readFileSync(
    new URL(
      "../src/kronika_capture/_assets/extension/src/adapters/pack_v5.json",
      import.meta.url
    ),
    "utf8"
  )
);

test("protocol version stays at 1", () => {
  assert.equal(PROTO_VERSION, 1);
});

test("durable capture capabilities and typed lifecycle errors are explicit", () => {
  assert.deepEqual(CLIENT_CAPABILITIES, ["durable_submission", "admin_resume"]);
  for (const code of ["E_BROWSER_UNAVAILABLE", "E_NEEDS_ADMIN", "E_SERVICE_LIMIT",
    "E_IDEMPOTENCY_CONFLICT", "E_AMBIGUOUS_SEND", "E_JOURNAL_UNAVAILABLE", "E_RESULT_TOO_LARGE"]) {
    assert.ok(ERROR_CODES.includes(code));
  }
  assert.ok(!ERROR_CODES.includes("E_ATTACHMENT_INVALID"));
  assert.ok(!ERROR_CODES.includes("E_RESULT_EXPIRED"));
});

test("upload_input locator is retained and unused by the ask gate", () => {
  assert.ok(pack.locators.upload_input);
  const blocked = unsupportedJob({
    kind: "ask",
    mode: null,
    prompt: "hello",
    files: ["fid"],
  });
  assert.equal(blocked.code, "E_UPLOAD_FAILED");
  assert.match(blocked.message, /file upload is not available in this build/);
});

test("removed modes and kinds fail closed", () => {
  assert.equal(
    unsupportedJob({ kind: "ask", mode: "web_search", prompt: "x" }).code,
    "E_WEB_SEARCH_UNAVAILABLE"
  );
  assert.equal(
    unsupportedJob({ kind: "ask", mode: "deep_research", prompt: "x" }).code,
    "E_DEEP_RESEARCH_UNAVAILABLE"
  );
  assert.equal(
    unsupportedJob({ kind: "ask", mode: "other", prompt: "x" }).code,
    "E_INTERNAL"
  );
  assert.equal(unsupportedJob({ kind: "ingest", mode: null, prompt: "x" }).code, "E_INTERNAL");
  assert.equal(
    unsupportedJob({ kind: "ask", mode: null, prompt: "x", files: [] }),
    null
  );
});
