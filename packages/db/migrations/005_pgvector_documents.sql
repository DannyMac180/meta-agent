-- Enable pgvector extension and create documents table for RAG
create extension if not exists vector;

create table if not exists documents (
  id uuid primary key default gen_random_uuid(),
  text text not null,
  meta jsonb,
  embedding vector(1536)
);

create index if not exists idx_documents_embedding on documents using ivfflat (embedding vector_l2_ops) with (lists = 100);
