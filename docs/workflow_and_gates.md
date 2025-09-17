# Builder Workflow & Quality Gates

## Workflow (Mastra graph)
1) **Interview → Spec**  
2) **Template select** (by use-case)  
3) **Scaffold project** (Mastra structure)  
4) **Wire tools/routes/config** (from Spec)  
5) **Generate tests/evals** (from `spec.tests`)  
6) **Quality gates** (fail → repair loop to step 4)  
7) **Package** (zip; docker if selected)  
8) **Smoke + acceptance evals** (fail → repair loop)  
9) **Publish artifacts + register version**  

### Idempotency
- Each node commits an artifact/state record; retries resume from last successful node.

### Budgets
- Honor `budget.buildBudgetUsd`. If near limit: warn; if exceeded: stop and return a **Build Report** with partial artifacts and next‑step suggestions.

## Quality Gates (default)
- **Type-check**: `tsc --noEmit`
- **Lint/format**: ESLint + Prettier
- **Unit tests**: Vitest (generated)
- **Security**: `npm audit` (fail on high/critical), Semgrep baseline
- **License**: allow‑list scan
- **Evals**: acceptance tests from spec (quick string/behavior checks)
- **Vector sanity**: verify embeddings dim matches `indexTable` schema

## Packaging
- **zip**: always generated and uploaded as builder artifact step `package:zip`.
- **docker**: optional; builds a `node:20-alpine` image, exports an OCI tarball, and records it as step `package:docker`.
- Artifacts use `artifactKey` (`scaffolds/{userId}/{draftId}/{buildId}/...`) for storage and idempotency.
- Set `MOCK_DOCKER_BUILD=1` to bypass Docker CLI during local tests.

## Runner Modes
- **Node Worker**: fastest path; good for typical agents.
- **Docker**: isolation; **mandatory for Code Interpreter**.

## Logs/Traces
- Stream build/run logs to UI; persist traces (OTEL) with run IDs.
