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
Sairam knowledge base/
```

The API ingests changed markdown files into Chroma on startup.

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

LM Studio should be running its OpenAI-compatible server at `http://localhost:1234/v1` with `qwen3.5-4b` loaded.
