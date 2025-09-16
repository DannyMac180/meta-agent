# Tools & Templates

## Day‑1 Tools

### HTTP
- Enforced **egress allow‑list** (from spec).
- Returns status, headers, truncated body; json/text hint.

### Web Search
- Provider: **Tavily** by default (configurable).
- Returns concise results with source URLs.

### Code Interpreter (JS)
- **Always runs in Docker** (no `node:vm` for untrusted code).
- Defaults: `timeoutMs=8000`, `memMb=256`, `network=false`.
- Optional NPM packages allow‑list (from spec).
- **Security Features:**
  - Network isolation by default (`--network=none`)
  - Resource quotas (CPU: 0.5 core, Memory: configurable, Disk: 100MB temp)
  - Non-root execution (UID 1001)
  - Package validation and allow-lists
  - Output size limits (50KB stdout, 25KB stderr)
  - Container cleanup and timeout enforcement

### Vector Store (pgvector)
- `indexTable` required.
- Basic ops: upsert, similarity search (cosine).
- Requires `embeddings` config (`dim` must match schema).

## Templates (v1)
- `chatbot` — REST + chat, optional RAG.
- `web-automation` — HTTP + web search workflows.
- `api-copilot` — agent that calls external APIs.
- (Optional) `slack-bot`, `scheduled-job`.

## Generated Agent Structure (Mastra)
- src/mastra/{agents,tools,workflows}/
- src/server/ (optional Hono/Express routes)
- tests/{unit,evals}/


## Example: Code Interpreter tool usage
```ts
import { codeTool } from "@metaagent/tools-code";

// Basic execution
const result = await codeTool.execute({
  code: "console.log('Hello World!'); Math.sqrt(16);",
  timeoutMs: 5000,
  memMb: 128
});

// With packages
const resultWithPackages = await codeTool.execute({
  code: "const _ = require('lodash'); console.log(_.isEmpty({}));",
  packages: ["lodash"],
  timeoutMs: 10000
});

// Result structure
interface CodeExecutionResult {
  success: boolean;
  exitCode?: number;
  stdout: string;      // Console output
  stderr: string;      // Error output  
  executionTimeMs: number;
  error?: string;      // Execution error
  truncated?: {        // If output was truncated
    stdout?: boolean;
    stderr?: boolean;
  };
}
```

## Example: HTTP tool skeleton
```ts
import { z } from "zod";

export const httpTool = {
  name: "http_fetch",
  description: "HTTP requests to allowed hosts",
  schema: z.object({
    method: z.enum(["GET","POST","PUT","PATCH","DELETE"]),
    url: z.string().url(),
    headers: z.record(z.string()).optional(),
    body: z.string().optional()
  }),
  run: async (args: any, ctx: { allow: string[] }) => {
    const { method, url, headers, body } = args;
    const host = new URL(url).host;
    if (!ctx.allow?.some(h => host === h || host.endsWith(`.${h}`))) {
      throw new Error("Egress to this host is not allowed");
    }
    const res = await fetch(url, { method, headers, body });
    const text = await res.text();
    return {
      status: res.status,
      headers: Object.fromEntries(res.headers),
      body: text.slice(0, 20_000),
      format: res.headers.get("content-type")?.includes("json") ? "json" : "text"
    };
  }
};
