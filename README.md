# Sairam Aegis

Full-stack RAG application split into:

- `Aegis_backend`: FastAPI, LangChain, Supabase Postgres/pgvector, local auth, chat APIs.
- `Aegis_frontend`: Next.js app for login, chat, and projects.
- `Aegis_runner`: Mac-side local LLM bridge for hosted backend deployments.

## Local Run Order

1. Configure Supabase and apply SQL migrations from `Aegis_backend/supabase/migrations`.
2. Put markdown files inside `Aegis_backend/Sairam_knowledge_base`.
3. Start Ollama and make sure your model is available:

```bash
ollama list
```

4. Configure `Aegis_backend/.env`:

```bash
APP_NAME="Sairam Aegis API"
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:3000

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
SUPABASE_SECRET_KEY=sb_secret_xxx

LLM_PROVIDER=openai_compatible
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b
LOCAL_LLM_API_KEY=ollama

RAG_INGEST_ON_STARTUP=true
KNOWLEDGE_BASE_DIR="./Sairam_knowledge_base"
INGESTION_MANIFEST_PATH="./storage/ingestion_manifest.json"

EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIMENSION=1024
RUNNER_REQUEST_TIMEOUT_SECONDS=180
```

5. Run the backend:

```bash
cd Aegis_backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

6. Configure frontend env:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxx
```

7. Run the frontend:

```bash
cd Aegis_frontend
npm install
npm run dev
```

The frontend routes are `/login`, `/chat`, and `/projects`.

## Hosted Prototype

```text
Vercel frontend
  -> DigitalOcean App Platform backend
  -> Supabase Postgres + pgvector
  -> Mac runner
  -> Ollama or another OpenAI-compatible local LLM
```

Hosted backend uses the same Supabase envs, with:

```bash
LLM_PROVIDER=runner
RUNNER_SHARED_SECRET=replace-with-a-long-random-secret
```

Mac runner environment:

```bash
BACKEND_WS_URL=wss://api.yourdomain.com/runners/connect
RUNNER_SHARED_SECRET=replace-with-the-backend-secret
LOCAL_LLM_BASE_URL=http://localhost:11434/v1
LOCAL_LLM_MODEL=llama3.1:8b
LOCAL_LLM_API_KEY=ollama
```

Apply all Supabase migrations, including the pgvector migration, before starting the backend.
