-- Session helper to set current app user ID
create or replace function set_app_user(uid uuid) returns void
language sql as $$ select set_config('app.current_user_id', uid::text, false) $$;

-- Enable RLS on tables (do not FORCE yet)
alter table if exists app_users enable row level security;
alter table if exists agents enable row level security;
alter table if exists agent_versions enable row level security;
alter table if exists run_history enable row level security;
alter table if exists user_settings enable row level security;

-- Policies (drop existing first, then create new)
drop policy if exists app_users_self on app_users;
create policy app_users_self on app_users
  using (id = current_setting('app.current_user_id', true)::uuid);

drop policy if exists agents_owner on agents;
create policy agents_owner on agents
  using (owner_user_id = current_setting('app.current_user_id', true)::uuid);

drop policy if exists agent_versions_owner on agent_versions;
create policy agent_versions_owner on agent_versions
  using (exists (
    select 1 from agents a
    where a.id = agent_versions.agent_id
      and a.owner_user_id = current_setting('app.current_user_id', true)::uuid
  ));

drop policy if exists run_history_visible on run_history;
create policy run_history_visible on run_history
  using (
    runner_user_id = current_setting('app.current_user_id', true)::uuid
    or exists (
      select 1 from agent_versions v
      join agents a on a.id = v.agent_id
      where v.id = run_history.agent_version_id
        and a.owner_user_id = current_setting('app.current_user_id', true)::uuid
    )
  );

drop policy if exists user_settings_owner on user_settings;
create policy user_settings_owner on user_settings
  using (owner_user_id = current_setting('app.current_user_id', true)::uuid);
