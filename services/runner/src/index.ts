import Fastify from "fastify";
import dotenv from "dotenv";
import { logger } from "@metaagent/toolkit";
import { createAgentExecWorker } from "@metaagent/queue";
import { httpTool } from "@metaagent/tools-http";
import { webSearchTool } from "@metaagent/tools-websearch";
import { vectorTool } from "@metaagent/tools-vector";

dotenv.config();

export function createServer() {
  const app = Fastify({ logger });

  app.get("/healthz", async () => ({ status: "ok" }));
  app.get("/readyz", async () => ({ status: "ready" }));

  // Tools endpoint for simple execution
  app.post<{ Params: { name: string } }>("/tools/:name", async (req, reply) => {
    const name = req.params.name;
    const args = req.body as any;
    try {
      if (name === 'http') {
        const res = await httpTool(args);
        return res;
      }
      if (name === 'webSearch') {
        const res = await webSearchTool(args);
        return res;
      }
      if (name === 'vector') {
        const res = await vectorTool(args);
        return res;
      }
      reply.code(404);
      return { error: 'tool not found' };
    } catch (e: any) {
      reply.code(400);
      return { error: e?.message || 'tool error' };
    }
  });

  return app;
}

const app = createServer();

if (process.env.NODE_ENV !== 'test' && !process.env.VITEST_WORKER_ID) {
  // Start BullMQ worker
  const worker = createAgentExecWorker(async (data) => {
    app.log.info({ runId: data.runId, prompt: data.prompt }, "processing job");
    // mock execution
    const output = `echo: ${data.prompt}`;
    return { runId: data.runId, output };
  });

  const shutdown = async () => {
    await worker.close();
    await app.close();
    process.exit(0);
  };
  process.on("SIGTERM", shutdown);
  process.on("SIGINT", shutdown);

  const port = Number(process.env.RUNNER_PORT ?? 3102);
  app.listen({ port, host: "0.0.0.0" }).catch((err) => {
    app.log.error(err);
    process.exit(1);
  });
}

