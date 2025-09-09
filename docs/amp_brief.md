# Amp Brief — MetaAgent v2.0

## Objective
Implement MetaAgent v2.0 as per the docs:
- Remix web app (Spec Panel, Catalog, Run Console)
- Mastra Builder workflow (interview → spec → scaffold → wire → tests → gates → package → register)
- Tools: HTTP, Web Search (Tavily), Code Interpreter (Dockerized JS), Vector (pgvector)
- Private per-user catalog (see `data_model.sql`)
- Electron Mac app (local runner)

## Constraints & Policies
- TypeScript-only; Mastra for all agents.
- **Code Interpreter must run in Docker**; do not use `node:vm` for untrusted code.
- Enforce `buildBudgetUsd` during builder runs.
- HTTP egress allow‑list required.

## Deliverables (incremental)
- Week-by-week per `delivery_plan.md`; each PR adds a demo scenario in `apps/web/docs/demos.md`.

## Acceptance Tests
1. Build a `web-automation` agent; packaging succeeds; acceptance eval passes.
2. Run from Catalog; logs/traces visible; expected output produced.
3. Code Interpreter executes snippet within time/mem limits; network blocked by default.
4. RAG demo: ingest small docs, query returns a source-backed answer.
5. Electron app runs offline and executes a local agent.

## Nice-to-haves (if time)
- Simple OTEL traces viewer link from run detail.
- “Repair loop” summary in the Build Report when gates fail.
