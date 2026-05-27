# Sairam Aegis

Full-stack RAG application split into:

- `Aegis backend`: FastAPI, LangChain, LM Studio, Chroma, Supabase migrations.
- `Aegis frontend`: Next.js three-page app for login, chat, and projects.

## Local Run Order

1. Start Supabase or configure an existing Supabase project.
2. Apply SQL migrations from `Aegis backend/supabase/migrations`.
3. Put markdown files inside `Aegis backend/Sairam knowledge base`.
4. Start LM Studio and enable its OpenAI-compatible server at `http://localhost:1234/v1`.
5. Run the backend:

```bash
cd "Aegis backend"
uv python install 3.11
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

6. Run the frontend:

```bash
cd "Aegis frontend"
npm install
npm run dev
```

The frontend routes are `/login`, `/chat`, and `/projects`.
