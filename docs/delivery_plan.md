# Delivery Plan (8 Weeks)

## Week 1 — Monorepo & Infra
- Scaffold pnpm+turbo workspace; apps/services/packages.
- Remix hello world; auth stub; health endpoints.
- DB up with migrations; RLS scaffolding.
- BullMQ + Redis wired.
**Acceptance:** `pnpm dev` runs web + builder + runner; DB tests green.

## Week 2 — Spec & Interview ✅
- `packages/spec`: types + zod validators.
- UI Spec Panel (live validation).
- Builder nodes: interview->spec (basic), template selection.
**Acceptance:** Save draft specs; see in “My Catalog” as draft.

## Week 3 — Templates & Scaffolder
- `packages/templates`: chatbot, web-automation, api-copilot.
- Builder: scaffold project to object storage; inject placeholders.
**Acceptance:** Zip contains CLI-valid Mastra project.

## Week 4 — Tools: HTTP, Web Search, Vector
- Implement tools; wire to generated agents.
- pgvector migration + basic ingestion/query.
- Egress allow‑list enforced.
**Acceptance:** Allow‑listed HTTP works; simple RAG round‑trip passes.

## Week 5 — Code Interpreter + Gates
- Containerized code tool (JS); quotas/timeouts; no network by default.
- Gates: tsc/eslint/vitest, audit+semgrep, license scan.
- Acceptance evals generator.
**Acceptance:** Code tool executes safely; failing tests block packaging.

## Week 6 — Packaging, Smoke Runs, Catalog UI
- zip + docker packaging; smoke/acceptance runs.
- Register version; Remix catalog & run console with logs.
**Acceptance:** “Build” → version listed; “Run” → logs + output.

## Week 7 — Electron (Mac) & Local Runner
- Electron shell; local runner settings.
- Build DMG with Electron Forge.
**Acceptance:** Mac app runs offline; executes a generated agent locally.

## Week 8 — Hardening & Docs
- End-to-end demos; budget ceiling enforcement + report.
- Improve traces; finalize READMEs and `.env.example`.
**Acceptance:** Two recorded demos; docs polished; CI green.