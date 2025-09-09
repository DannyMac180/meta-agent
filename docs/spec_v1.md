```markdown
# AgentSpecV1

This is the **single source of truth** for building an agent. The Builder consumes this spec deterministically.

## TypeScript types
```ts
export type RuntimeTarget = "local" | "docker" | "node-server";
export type InterfaceKind = "rest" | "chat" | "cli" | "scheduler";

export interface BudgetPolicy {
  buildBudgetUsd?: number;   // limit for builder's end-to-end process
  runBudgetUsd?: number;     // optional monthly cap enforced by Runner (later)
}

export interface ModelConfig {
  provider: "openai" | "anthropic" | "mistral" | "google" | "azure" | "local";
  model: string;
}

export interface EmbeddingsConfig {
  provider: ModelConfig["provider"];
  model: string;
  dim: number;               // must match pgvector schema
}

export interface ToolHttp { kind: "http"; baseUrl?: string; allow?: string[] }
export interface ToolWebSearch { kind: "web_search"; provider?: "tavily" | "serper" }
export interface ToolCode { kind: "code"; language?: "javascript"; timeoutMs?: number; memMb?: number; packages?: string[]; network?: boolean }
export interface ToolVector { kind: "vector"; driver: "pgvector"; indexTable: string }

export type ToolSpec = ToolHttp | ToolWebSearch | ToolCode | ToolVector;

export interface AgentSpecV1 {
  meta: { name: string; version: string; description?: string };
  runtime: { target: RuntimeTarget };
  interfaces: InterfaceKind[];
  models: ModelConfig;             // Mastra adapters
  embeddings?: EmbeddingsConfig;   // required if using vector/RAG
  tools: ToolSpec[];
  knowledge?: {
    rag?: boolean;
    indexTable?: string;           // if omitted, use ToolVector.indexTable
    chunk?: { size: number; overlap: number };
  };
  budget?: BudgetPolicy;
  policies?: { egressAllowlist?: string[]; pii?: "block" | "redact" | "allow" };
  tests: Array<{ name: string; prompt: string; mustInclude?: string[] }>;
  deployment?: { envVars?: string[]; secrets?: string[] };
}
