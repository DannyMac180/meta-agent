-- Update spec_drafts table to support builder nodes feature
-- Add fields needed for interview workflow

-- Add new columns for builder nodes
alter table spec_drafts 
add column if not exists template_id text,
add column if not exists title text,
add column if not exists is_draft boolean default true,
add column if not exists status text default 'DRAFT' check (status in ('DRAFT', 'PUBLISHED'));

-- Migrate existing data: copy name to title if title is null
update spec_drafts set title = name where title is null;

-- Make title not null after migration
alter table spec_drafts alter column title set not null;

-- Add index for template queries
create index if not exists idx_spec_drafts_template on spec_drafts(template_id);

-- Add index for status queries
create index if not exists idx_spec_drafts_status on spec_drafts(status, updated_at desc);

-- Update the schema comment
comment on table spec_drafts is 'Agent specification drafts created through builder interview process';
comment on column spec_drafts.template_id is 'ID of template used to create this draft';
comment on column spec_drafts.title is 'User-friendly title for the draft';
comment on column spec_drafts.is_draft is 'Whether this is still a draft (true) or published (false)';
comment on column spec_drafts.status is 'Status of the draft: DRAFT or PUBLISHED';
