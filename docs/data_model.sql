-- USERS
create table if not exists app_users (
  id uuid primary key,
  email text unique not null,
  created_at timestamptz default now()
);

-- AGENTS (logical)
create table if not exists agents (
  id uuid primary key,
  owner_user_id uuid not null references app_users(id) on delete cascade,
  name text not null,
  slug text not null,
  visibility text not null default 'private', -- future: org/shared/public
  current_version_id uuid,
  created_at timestamptz default now()
);

-- VERSIONS (immutable)
create table if not exists agent_versions (
  id uuid primary key,
  agent_id uuid not null references agents(id) on delete cascade,
  semver text not null,
  spec jsonb not null,
  artifact_uri text not null,           -- zip or docker ref
  build_status text not null,           -- queued|success|failed
  build_cost_usd numeric(10,4),
  created_at timestamptz default now()
);

-- RUNS
create table if not exists run_history (
  id uuid primary key,
  agent_version_id uuid not null references agent_versions(id) on delete cascade,
  runner_user_id uuid not null references app_users(id),
  inputs jsonb,
  outputs_uri text,
  traces_uri text,
  status text,                          -- running|success|failed
  cost_usd numeric(10,4),
  started_at timestamptz default now(),
  finished_at timestamptz
);

-- INTERNAL TEMPLATE CATALOG
create table if not exists templates (
  id uuid primary key,
  key text unique not null,             -- e.g., "chatbot", "web-automation"
  description text not null,
  repo_uri text not null                -- monorepo path or tarball
);

-- USER SETTINGS
create table if not exists user_settings (
  owner_user_id uuid primary key references app_users(id) on delete cascade,
  default_build_budget_usd numeric(10,2) default 2.00,
  default_model_provider text,
  default_model_name text
);

-- Suggested indices
create index if not exists idx_agents_owner on agents(owner_user_id);
create index if not exists idx_versions_agent on agent_versions(agent_id);
create index if not exists idx_runs_version on run_history(agent_version_id);

-- (Optional) RLS policy scaffolding (enable after wiring auth context)
-- alter table agents enable row level security;
-- create policy agents_owner on agents using (owner_user_id = current_setting('app.current_user_id')::uuid);
