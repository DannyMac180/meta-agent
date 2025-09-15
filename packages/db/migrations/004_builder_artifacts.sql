-- Builder Artifacts table to store scaffold outputs
create table if not exists builder_artifacts (
  id uuid primary key default gen_random_uuid(),
  draft_id uuid not null references spec_drafts(id) on delete cascade,
  build_id text not null,
  step text not null default 'scaffold',
  bucket text not null,
  object_key text not null,
  size_bytes bigint,
  etag text,
  created_at timestamptz default now()
);

-- Ensure one artifact per draft per step (idempotent for retries)
create unique index if not exists uq_builder_artifacts_draft_step on builder_artifacts(draft_id, step);

-- For lookup
create index if not exists idx_builder_artifacts_draft on builder_artifacts(draft_id, created_at desc);
