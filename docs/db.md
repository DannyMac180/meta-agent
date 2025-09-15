# Database setup (local + CI)

Prereqs: Docker Desktop or Podman, pnpm.

1) Start services
- pnpm db:up
- DATABASE_URL is expected in your env (see .env.example)

2) Migrations
- pnpm db:migrate
- Optionally inspect with: pnpm db:studio

3) Packages
- DB client lives in packages/db (drizzle config, migrations, and a node-postgres client)

4) RLS notes
- RLS policies are scaffolded (001_rls_scaffold.sql) but not forced yet.
- Set session user per request: select set_config('app.current_user_id', '<uuid>', false);
- Week 3 will wire auth and enable FORCE RLS.

5) Troubleshooting
- Postgres: docker logs metaagent-postgres
- Reset: pnpm db:down && pnpm db:up

6) pgvector (Week 4)
- Image: infra uses pgvector/pgvector:pg15 to provide the extension.
- Migrations: 005_pgvector_documents.sql creates documents table; 006_pgvector_documents_cosine.sql recreates IVFFLAT index with vector_cosine_ops and runs ANALYZE.
- Commands: pnpm db:down && pnpm db:up && pnpm db:migrate  (Podman: pnpm db:down:podman && pnpm db:up:podman && pnpm db:migrate)
- Verify extension: psql -h localhost -U postgres -d metaagent -c "select extname from pg_extension;" (should include "vector")
- Verify index: in psql, \d+ documents (index should be ivfflat on embedding using vector_cosine_ops)

Acceptance (Week 4 bullet 2)
- Vector extension present and migrations applied without error.
- Ingest/query round-trip works via scripts: pnpm ingest README.md; pnpm query "question" returns a result with score ≥ 0.9.
- Workspace tests for @metaagent/tools-vector pass (OpenAI calls mocked).
