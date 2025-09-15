-- Ensure pgvector index uses cosine distance to match application (<=>)
begin;

-- Drop the existing L2 index if present
drop index if exists idx_documents_embedding;

-- Recreate IVFFLAT index using cosine ops and recommended lists
create index if not exists idx_documents_embedding
  on documents using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- Gather statistics for the planner
analyze documents;

commit;
