import { zodToJsonSchema } from "zod-to-json-schema";
import { AgentSpecSchema } from "@metaagent/spec";

export function generateJsonSchema() {
  return zodToJsonSchema(AgentSpecSchema, {
    name: "AgentSpec",
    $refStrategy: "none", // Inline all refs for Monaco
  });
}

export const AGENT_SPEC_JSON_SCHEMA = generateJsonSchema();
