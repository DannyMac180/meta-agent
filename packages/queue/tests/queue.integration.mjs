import assert from 'node:assert/strict';
import { setTimeout as delay } from 'node:timers/promises';
import Redis from 'ioredis';
import { agentExecQueue, enqueueAgentExec, createAgentExecWorker, redisOptions } from '../dist/index.js';

async function redisAvailable() {
  const client = new Redis({ ...redisOptions, connectTimeout: 500, retryStrategy: () => null });
  try {
    const res = await client.ping();
    return res === 'PONG';
  } catch {
    return false;
  } finally {
    client.disconnect();
  }
}

async function main() {
  if (process.env.CI) {
    console.log('[queue.integration] SKIP in CI');
    process.exit(0);
  }

  if (!(await redisAvailable())) {
    console.log('[queue.integration] SKIP: no Redis available');
    process.exit(0);
  }

  const runId = `itest-${Date.now()}`;
  let processed = null;

  const worker = createAgentExecWorker(async (data) => {
    processed = { ...data, output: `ok:${data.prompt}` };
    return { runId: data.runId, output: processed.output };
  }, { concurrency: 1 });

  const timeoutMs = 5000;
  const start = Date.now();

  await enqueueAgentExec({ runId, prompt: 'ping' });

  while (!processed && Date.now() - start < timeoutMs) {
    await delay(50);
  }

  try {
    assert.ok(processed, 'Job was not processed in time');
    assert.equal(processed.runId, runId);
    assert.equal(processed.output, 'ok:ping');
    console.log('[queue.integration] PASS');
  } finally {
    await worker.close();
    await agentExecQueue.drain();
    await agentExecQueue.close();
  }
}

main().catch((err) => {
  console.error('[queue.integration] FAIL', err);
  process.exit(1);
});
