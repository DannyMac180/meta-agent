export * from "./enums.js";

// types
export * from "./types/common.js";
export * from "./types/variable.js";
export * from "./types/prompt.js";
export * from "./types/model.js";
export * from "./types/tool.js";
export * from "./types/agent.js";
export * from "./types/draft.js";
export * from "./types/eval.js";

// validators
export * from "./validators/variable.js";
export * from "./validators/prompt.js";
export * from "./validators/model.js";
export * from "./validators/tool.js";
export * from "./validators/agent.js";
export * from "./validators/draft.js";
export * from "./validators/eval.js";

// tool definitions
export * from "./tools/definitions.js";

// helpers
import { AgentSpecSchema } from "./validators/agent.js";
import type { AgentSpec } from "./types/agent.js";

export function parseAgentSpec(json: unknown): AgentSpec {
  return AgentSpecSchema.parse(json) as AgentSpec;
}

export function isAgentSpec(obj: unknown): obj is AgentSpec {
  const res = AgentSpecSchema.safeParse(obj);
  return res.success;
}

// draft helpers
export * from "./helpers/draft.js";

