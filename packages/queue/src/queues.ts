import { Queue, Worker, type JobsOptions } from "bullmq";
import { redisOptions } from "./redis.js";
import type {
  AgentExecData,
  AgentExecResult,
  DraftAutosaveData,
  DraftAutosaveResult,
  BuilderScaffoldJob,
  BuilderScaffoldResult,
} from "./types.js";

export const AGENT_EXEC_QUEUE = "agent-exec";
export const DRAFT_AUTOSAVE_QUEUE = "draft-autosave";
export const BUILDER_SCAFFOLD_QUEUE = "builder-scaffold";

export const agentExecQueue = new Queue<AgentExecData>(AGENT_EXEC_QUEUE, {
  connection: redisOptions,
});

export const draftAutosaveQueue = new Queue<DraftAutosaveData>(DRAFT_AUTOSAVE_QUEUE, {
  connection: redisOptions,
});

export const builderScaffoldQueue = new Queue<BuilderScaffoldJob>(BUILDER_SCAFFOLD_QUEUE, {
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

export function enqueueDraftAutosave(
  data: DraftAutosaveData,
  opts?: JobsOptions
) {
  const jobId = data.draft.id ? `draft:${data.userId}:${data.draft.id}` : undefined;
  return draftAutosaveQueue.add("autosave", data, {
    jobId,
    removeOnComplete: 500,
    attempts: 5,
    backoff: { type: "exponential", delay: 2000 },
    ...opts,
  });
}

export function enqueueBuilderScaffold(
  data: BuilderScaffoldJob,
  opts?: JobsOptions
) {
  const jobId = `scaffold:${data.userId}:${data.draftId}`;
  return builderScaffoldQueue.add("scaffold", data, {
    jobId,
    removeOnComplete: 100,
    attempts: 5,
    backoff: { type: "exponential", delay: 2000 },
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

export function createDraftAutosaveWorker(
  handler: (data: DraftAutosaveData) => Promise<DraftAutosaveResult>,
  opts?: { concurrency?: number }
) {
  const worker = new Worker<DraftAutosaveData>(
    DRAFT_AUTOSAVE_QUEUE,
    async (job) => handler(job.data),
    { connection: redisOptions, concurrency: opts?.concurrency ?? 10 }
  );
  return worker;
}

export function createBuilderScaffoldWorker(
  handler: (data: BuilderScaffoldJob) => Promise<BuilderScaffoldResult>,
  opts?: { concurrency?: number }
) {
  const worker = new Worker<BuilderScaffoldJob>(
    BUILDER_SCAFFOLD_QUEUE,
    async (job) => handler(job.data),
    { connection: redisOptions, concurrency: opts?.concurrency ?? 3 }
  );
  return worker;
}
