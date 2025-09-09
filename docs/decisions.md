# MetaAgent v2.0 — Decisions

- Framework: **Mastra** for the builder and all generated agents.
- Web UI: **Remix** (Node runtime), Tailwind + shadcn/ui (or equivalent).
- Desktop: **Electron** for Mac v1 (local runner included).
- Language: **TypeScript** only (no Python).
- Catalog: **Private per user** (sharing later).
- Day‑1 tools: **HTTP**, **Web Search (Tavily default)**, **Code Interpreter (JS)**, **Vector Store (pgvector)**.
- Models: **Mastra-supported providers** only by default; configurable per spec.
- Budgets: **Per-build** budget ceiling (stop with report when exceeded); optional per-agent run budget later.
- Runner: Node workers (fast path) or **Docker** (isolation). **Code Interpreter always in Docker**.
- Object storage: S3-compatible (MinIO in dev).
- Queueing: **BullMQ** (Redis).
- Security: RLS on DB; secrets injected at run/deploy time; HTTP egress allow‑list; no network in Code Interpreter unless enabled.
- MagicPath: **Developer-only** export/import into `packages/ui` (not part of product UI).
