"""Real loopback result delivery with a synthetic Node engine; no browser."""

import json
from pathlib import Path
import subprocess
import uuid

import pytest

from kronika_capture import config, errors
from kronika_capture.bridge.jobs import JobManager
from kronika_capture.bridge.store import Store
from test_bridge_security import bridge, _hello, _request


RUNNER_PROBE = r'''
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { BridgeClient } from "./src/kronika_capture/_assets/extension/src/headless/bridge_client.mjs";
import { executeOffer } from "./src/kronika_capture/_assets/extension/src/headless/runner.mjs";
import { RESULT_MAX_BYTES } from "./src/kronika_capture/_assets/extension/src/protocol.js";
const input = JSON.parse(readFileSync(0, "utf8"));
assert.equal(RESULT_MAX_BYTES, input.limit);
const client = new BridgeClient({url: `http://127.0.0.1:${input.port}`, token: input.token});
let executions = 0, deliveries = 0, oversized = 0, lostAck = false, firstId, failure;
const deliver = client.result.bind(client);
client.result = async (id, body) => {
  assert.ok(++deliveries <= 3);
  firstId ??= body.delivery_id;
  assert.equal(body.delivery_id, firstId);
  try { await deliver(id, body); }
  catch (error) {
    assert.equal(error.status, 413);
    assert.equal(error.code, "E_RESULT_TOO_LARGE");
    oversized++;
    throw error;
  }
  assert.equal(body.status, "failed");
  assert.equal(body.error_code, "E_RESULT_TOO_LARGE");
  assert.equal(body.answer, null);
  failure = body;
  if (!lostAck) { lostAck = true; throw new Error("synthetic lost acknowledgement"); }
};
class Engine {
  constructor(options) { Object.assign(this, options); }
  async run() {
    executions++;
    await this.emit("send_intent", {});
    await this.emit("send_confirmed", {response_id: randomUUID()});
    const answer = input.mode === "wire" ? "€".repeat(600)
      : input.mode === "unicode" ? "€".repeat(Math.ceil(RESULT_MAX_BYTES / 3))
      : "x".repeat(RESULT_MAX_BYTES - 1);
    assert.ok(answer.length < RESULT_MAX_BYTES);
    return {status: "done", answer, activity_stopped: true};
  }
}
const driver = {stops: 0, async stop() {this.stops++;}};
const result = await executeOffer({client, driver, pack: {}, job: input.job, Engine,
  sleep: async () => {}, signal: AbortSignal.timeout(10000)});
assert.equal(result.error_code, "E_RESULT_TOO_LARGE");
assert.equal(executions, 1);
assert.equal(driver.stops, 0);
assert.equal(deliveries, input.mode === "wire" ? 3 : 2);
assert.equal(oversized, input.mode === "wire" ? 1 : 0);
const read = await client.requestWithStatus("GET", `/v1/jobs/${input.job.job_id}`);
assert.equal(read.status, 200);
assert.equal(read.payload.job.status, "failed");
assert.equal(read.payload.job.result.error_code, "E_RESULT_TOO_LARGE");
await assert.rejects(deliver(input.job.job_id, {...failure, delivery_id: randomUUID()}),
  error => error.status === 409 && error.code === "E_IDEMPOTENCY_CONFLICT");
console.log(JSON.stringify({executions, deliveries, oversized, delivery_id: firstId}));
'''


@pytest.mark.parametrize("mode", ["unicode", "envelope", "wire"])
def test_oversized_runner_result_is_durable_typed_failure(bridge, monkeypatch, mode):
    _server, state, port = bridge
    limit = config.RESULT_MAX_BYTES
    if mode == "wire":
        # Exercise a real permanent HTTP rejection followed by small-envelope delivery.
        monkeypatch.setattr(config, "RESULT_MAX_BYTES", 1024)
    _hello(port, state.token)
    req = {"request_id": str(uuid.uuid4()), "prompt": "synthetic"}
    status, created = _request(port, "POST", "/v1/jobs", token=state.token, body=req)
    assert status == 200
    status, offered = _request(port, "GET", "/v1/next?wait=0", token=state.token)
    assert status == 200
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", RUNNER_PROBE],
        cwd=Path(__file__).resolve().parents[3],
        input=json.dumps({"port": port, "token": state.token, "job": offered["job"],
                          "mode": mode, "limit": limit}),
        text=True, capture_output=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    assert observed["executions"] == 1
    job_id = created["job_id"]
    assert state.jobs._jobs[job_id].delivery_id == observed["delivery_id"]
    assert state.jobs.create_job(req).status == "failed"
    assert state.jobs.next_offer(0, runner_id=offered["job"]["runner_id"],
                                 epoch=offered["job"]["epoch"]) is None
    state.jobs.journal.close()
    state.jobs = JobManager(Store(state.store.root))
    status, payload = _request(port, "GET", f"/v1/jobs/{job_id}", token=state.token)
    assert status == 200
    assert payload["job"]["status"] == "failed"
    assert payload["job"]["result"]["error_code"] == "E_RESULT_TOO_LARGE"
    assert payload["job"]["result"]["answer"] is None
    assert state.jobs._jobs[job_id].delivery_id == observed["delivery_id"]
    state.jobs.journal.close()


def test_result_vocabulary_reconciliation():
    assert "E_RESULT_TOO_LARGE" in errors.ERROR_CODES
    assert "E_ATTACHMENT_INVALID" not in errors.ERROR_CODES
    assert "E_RESULT_EXPIRED" not in errors.ERROR_CODES
