# Architecture

## Components
- **apps/web (Remix)**: chat + spec panel, catalog, run console, logs.
- **services/builder (Mastra)**: interview → spec → scaffold → wire tools → tests/evals → gates → package → register.
- **services/runner (Mastra)**: run agents in Node worker or Docker; manage logs/traces/cost.
- **packages/**: spec types, shared UI, tool implementations, codegen toolkit, templates.
- **infra/**: SQL migrations, Docker, local dev scripts.

## Authentication & Sessions
- Cookie-based sessions via Remix's `createCookieSessionStorage`
- Development mode: accepts any username via `/auth/login`
- Session utilities in `apps/web/app/utils/session.server.ts`: `getUserId()`, `requireUserId()`, `createUserSession()`, `logout()`
- Database RLS policies enforce user isolation via `app.current_user_id`

## Autosave System
- **Flow**: Interview panel → debounced autosave → API route → BullMQ queue → Builder worker → Database
- **Rate limiting**: 30 requests/minute per user
- **Payload validation**: Title required (max 200 chars), payload max 500KB
- **Job deduplication**: Uses `draft:${userId}:${draftId}` as job ID
- **Error handling**: Structured logging, graceful degradation
- **Worker**: `services/builder/src/handlers/draftAutosave.ts` handles upsert logic

## High-level diagram
```mermaid
graph TD
  R[Remix Web App] --> Chat[Requirements Chat + Spec]
  R --> Catalog[My Catalog]
  R --> Runs[Run Console]

  subgraph Builder (Mastra)
    B1[Interview->Spec]-->B2[Template Select]-->B3[Scaffold]
    B3-->B4[Wire Tools]-->B5[Tests/Evals]-->B6[Quality Gates]
    B6-->B7[Package]-->B8[Smoke+Acceptance]-->B9[Publish+Register]
    B6--fail-->B4
    B8--fail-->B4
  end

  subgraph Runner
    RW[Node Worker]
    RD[Docker]
  end

  R-->B1
  R-->RW
  R-->RD

  PG[(Postgres+pgvector)]
  OBJ[(Object Storage)]
  REDIS[(Redis/BullMQ)]
  OTEL[(Tracing/Logs)]

  B*-->OBJ
  B*-->REDIS
  RW-->PG
  RD-->PG
  RW-->OTEL
  RD-->OTEL
