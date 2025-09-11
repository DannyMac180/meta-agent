import Fastify from "fastify";
import dotenv from "dotenv";
import { logger } from "@metaagent/toolkit";

dotenv.config();

const app = Fastify({ logger });

app.get("/healthz", async () => ({ status: "ok" }));
app.get("/readyz", async () => ({ status: "ready" }));

const port = Number(process.env.RUNNER_PORT ?? 3102);
app.listen({ port, host: "0.0.0.0" }).catch((err) => {
  app.log.error(err);
  process.exit(1);
});

