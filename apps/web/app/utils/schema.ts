import { zodToJsonSchema } from "zod-to-json-schema";
import { AgentSpecSchema } from "@metaagent/spec";

export function generateJsonSchema() {
  return zodToJsonSchema(AgentSpecSchema, {
    name: "AgentSpec",
    $refStrategy: "none", // Inline all refs for Monaco
  });
}

export const AGENT_SPEC_JSON_SCHEMA = generateJsonSchema();

// simple debounce helper
export function debounce<T extends (...args: any[]) => void>(fn: T, wait = 300) {
  let timeout: any;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), wait);
  };
}
