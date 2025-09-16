import Fastify from "fastify";
import dotenv from "dotenv";
import { logger } from "@metaagent/toolkit";
import { enqueueAgentExec, createDraftAutosaveWorker, createBuilderScaffoldWorker } from "@metaagent/queue";
import { handleDraftAutosave } from "./handlers/draftAutosave.js";
import { handleBuilderScaffold } from "./handlers/handleScaffoldJob.js";
import { validateAllowList } from "@metaagent/tools-http";

dotenv.config();

const app = Fastify({ logger });

// Validate egress allow-list configuration on startup
const validation = validateAllowList();
if (!validation.isValid) {
  app.log.warn(`[SECURITY] Allow-list validation: ${validation.error}`);
} else {
  app.log.info('[SECURITY] Egress allow-list configured and validated');
}

app.get("/healthz", async () => ({ status: "ok" }));
app.get("/readyz", async () => ({ status: "ready" }));

app.post("/jobs/demo", async () => {
  const runId = `demo-${Date.now()}`;
  await enqueueAgentExec({ runId, prompt: "Hello from builder" });
  return { enqueued: true, runId };
});

// Start Workers
createDraftAutosaveWorker(handleDraftAutosave);
createBuilderScaffoldWorker(handleBuilderScaffold);

const port = Number(process.env.BUILDER_PORT ?? 3101);
app.listen({ port, host: "0.0.0.0" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});

