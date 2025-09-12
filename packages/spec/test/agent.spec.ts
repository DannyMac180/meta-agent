import { describe, it, expect } from "vitest";
import { AgentSpecSchema } from "../src/validators/agent";
import { ProviderEnum } from "../src/enums";

const base = {
  specVersion: "0.1.0",
  meta: {
    id: "01ARZ3NDEKTSV4RRFFQ69G5FAV",
    name: "sample-agent",
    description: "test agent",
    version: "0.0.1",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    tags: ["test"],
  },
  variables: [
    { key: "topic", type: "string", required: true },
    { key: "mode", type: "enum", enumValues: ["short", "long"], required: false },
  ],
  prompt: {
    template: "Write about {{topic}} in {{mode}} mode.",
  },
  model: {
    provider: "openai" as (typeof ProviderEnum)[number],
    model: "gpt-4o-mini",
    maxTokens: 1024,
    temperature: 0.2,
  },
  tools: [
    { kind: "http", allowDomains: ["https://example.com"] },
  ],
  limits: {
    timeoutSec: 60,
    budgetUsd: 1,
  },
};

describe("AgentSpecSchema", () => {
  it("parses valid spec", () => {
    const res = AgentSpecSchema.safeParse(base);
    expect(res.success).toBe(true);
  });

  it("fails on undeclared variable in template", () => {
    const bad = { ...base, prompt: { template: "Hello {{unknown}}" } };
    const res = AgentSpecSchema.safeParse(bad);
    expect(res.success).toBe(false);
  });

  it("fails on invalid provider-specific limit", () => {
    const bad = { ...base, model: { ...base.model, maxTokens: 999999 } };
    const res = AgentSpecSchema.safeParse(bad);
    expect(res.success).toBe(false);
  });
});
