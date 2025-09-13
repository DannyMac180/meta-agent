-- Spec Drafts table for persisting user-authored agent specs
-- before they're built into versions

create table if not exists spec_drafts (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references app_users(id) on delete cascade,
  name text not null,
  spec jsonb not null,
  tags text[] default array[]::text[],
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Index for efficient owner queries sorted by recent activity
create index if not exists idx_spec_drafts_owner on spec_drafts(owner_user_id, updated_at desc);

-- Enable RLS on spec_drafts
alter table spec_drafts enable row level security;

-- RLS policy: users can only access their own drafts
drop policy if exists spec_drafts_owner on spec_drafts;
create policy spec_drafts_owner on spec_drafts
  using (owner_user_id = current_setting('app.current_user_id', true)::uuid);

-- Function to update updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on spec_drafts
drop trigger if exists update_spec_drafts_updated_at on spec_drafts;
create trigger update_spec_drafts_updated_at
  before update on spec_drafts
  for each row
  execute function update_updated_at_column();
