import Fastify from "fastify";
import dotenv from "dotenv";
import { logger } from "@metaagent/toolkit";
import { enqueueAgentExec } from "@metaagent/queue";

dotenv.config();

const app = Fastify({ logger });

app.get("/healthz", async () => ({ status: "ok" }));
app.get("/readyz", async () => ({ status: "ready" }));

app.post("/jobs/demo", async () => {
  const runId = `demo-${Date.now()}`;
  await enqueueAgentExec({ runId, prompt: "Hello from builder" });
  return { enqueued: true, runId };
});

const port = Number(process.env.BUILDER_PORT ?? 3101);
app.listen({ port, host: "0.0.0.0" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});

