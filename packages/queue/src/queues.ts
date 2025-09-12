import { Queue, Worker, type JobsOptions } from "bullmq";
import { redisOptions } from "./redis.js";
import type { AgentExecData, AgentExecResult } from "./types.js";

export const AGENT_EXEC_QUEUE = "agent-exec";

export const agentExecQueue = new Queue<AgentExecData>(AGENT_EXEC_QUEUE, {
  connection: redisOptions,
});

export function enqueueAgentExec(
  data: AgentExecData,
  opts?: JobsOptions
) {
  return agentExecQueue.add("run", data, {
    removeOnComplete: 100,
    attempts: 3,
    backoff: { type: "exponential", delay: 5000 },
    ...opts,
  });
}

export function createAgentExecWorker(
  handler: (data: AgentExecData) => Promise<AgentExecResult>,
  opts?: { concurrency?: number }
) {
  const worker = new Worker<AgentExecData>(
    AGENT_EXEC_QUEUE,
    async (job) => handler(job.data),
    { connection: redisOptions, concurrency: opts?.concurrency ?? 5 }
  );
  return worker;
}
