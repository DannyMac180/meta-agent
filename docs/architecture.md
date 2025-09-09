# Architecture

## Components
- **apps/web (Remix)**: chat + spec panel, catalog, run console, logs.
- **services/builder (Mastra)**: interview → spec → scaffold → wire tools → tests/evals → gates → package → register.
- **services/runner (Mastra)**: run agents in Node worker or Docker; manage logs/traces/cost.
- **packages/**: spec types, shared UI, tool implementations, codegen toolkit, templates.
- **infra/**: SQL migrations, Docker, local dev scripts.

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
