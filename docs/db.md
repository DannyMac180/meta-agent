# Database setup (local + CI)

Prereqs: Docker Desktop, pnpm.

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
