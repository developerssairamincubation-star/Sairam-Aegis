# Aegis Backend

FastAPI backend for the Aegis RAG application.

## Setup

```bash
uv python install 3.11
uv sync
cp .env.example .env
```

Fill in Supabase credentials in `.env`, then run migrations from `supabase/migrations` in your Supabase project.

## Knowledge Base

Place markdown files in:

```text
Sairam_knowledge_base/
```

When `RAG_INGEST_ON_STARTUP=true`, the API ingests changed markdown files into Supabase pgvector on startup.

## Local Run

Start Ollama and confirm the configured model exists:

```bash
ollama list
```

Then run:

```bash
uv run uvicorn app.main:app --reload --port 8000
```

For local direct Ollama mode:

```bash
LLM_PROVIDER=openai_compatible
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b
LOCAL_LLM_API_KEY=ollama
```

## Hosted Prototype

For DigitalOcean App Platform or a similar hosted container platform, build this directory with the included `Dockerfile`.

Required production variables:

```bash
APP_ENV=production
FRONTEND_ORIGIN=https://your-vercel-domain.vercel.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
SUPABASE_SECRET_KEY=sb_secret_xxx
LLM_PROVIDER=runner
RUNNER_SHARED_SECRET=replace-with-a-long-random-secret
RUNNER_REQUEST_TIMEOUT_SECONDS=180
```

Run the Supabase migrations before deployment. The pgvector migration creates `rag_documents`, `rag_chunks`, the HNSW vector index, and the `match_rag_chunks` RPC used by retrieval.

The hosted backend expects one Mac runner to connect to:

```text
wss://your-api-domain/runners/connect
```

Check `/rag/status` after startup to confirm Supabase chunk counts and runner connection state.
