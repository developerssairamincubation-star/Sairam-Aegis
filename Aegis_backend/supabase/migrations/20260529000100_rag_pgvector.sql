create extension if not exists vector with schema extensions;

create table if not exists public.rag_documents (
  id uuid primary key default gen_random_uuid(),
  source text not null unique,
  title text,
  sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.rag_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.rag_documents(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding vector(1024) not null,
  created_at timestamptz not null default now(),
  unique(document_id, chunk_index)
);

create index if not exists rag_chunks_document_id_idx
  on public.rag_chunks(document_id);

create index if not exists rag_chunks_embedding_hnsw_idx
  on public.rag_chunks
  using hnsw (embedding vector_cosine_ops);

drop trigger if exists set_rag_documents_updated_at on public.rag_documents;
create trigger set_rag_documents_updated_at
before update on public.rag_documents
for each row execute function public.set_updated_at();

create or replace function public.match_rag_chunks(
  query_embedding vector(1024),
  match_count int default 5
)
returns table (
  chunk_id text,
  document_id uuid,
  source text,
  title text,
  content text,
  metadata jsonb,
  similarity float
)
language sql
stable
as $$
  select
    d.source || ':' || c.chunk_index::text as chunk_id,
    d.id as document_id,
    d.source,
    d.title,
    c.content,
    c.metadata,
    1 - (c.embedding <=> query_embedding) as similarity
  from public.rag_chunks c
  join public.rag_documents d on d.id = c.document_id
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

alter table public.rag_documents enable row level security;
alter table public.rag_chunks enable row level security;

drop policy if exists "Authenticated users can read rag documents" on public.rag_documents;
create policy "Authenticated users can read rag documents"
on public.rag_documents for select
to authenticated
using (true);

drop policy if exists "Authenticated users can read rag chunks" on public.rag_chunks;
create policy "Authenticated users can read rag chunks"
on public.rag_chunks for select
to authenticated
using (true);
