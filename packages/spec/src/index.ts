export * from "./enums";

// types
export * from "./types/common";
export * from "./types/variable";
export * from "./types/prompt";
export * from "./types/model";
export * from "./types/tool";
export * from "./types/agent";

// validators
export * from "./validators/variable";
export * from "./validators/prompt";
export * from "./validators/model";
export * from "./validators/tool";
export * from "./validators/agent";

// helpers
import { AgentSpecSchema } from "./validators/agent";
import type { AgentSpec } from "./types/agent";

export function parseAgentSpec(json: unknown): AgentSpec {
  return AgentSpecSchema.parse(json) as AgentSpec;
}

export function isAgentSpec(obj: unknown): obj is AgentSpec {
  const res = AgentSpecSchema.safeParse(obj);
  return res.success;
}

