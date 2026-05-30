# Aegis Mac Runner

The runner is the bridge between the hosted backend and the local Mac LLM.
It opens an outbound WebSocket to the backend, receives generation jobs, calls a
local OpenAI-compatible server, and streams tokens back.

## Setup

```bash
cd Aegis_runner
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Start Ollama or another OpenAI-compatible local server, then run:

```bash
export BACKEND_WS_URL=wss://api.yourdomain.com/runners/connect
export RUNNER_SHARED_SECRET=replace-with-the-backend-secret
export LOCAL_LLM_BASE_URL=http://localhost:11434/v1
export LOCAL_LLM_MODEL=llama3.1:8b
export LOCAL_LLM_API_KEY=ollama
python runner.py
```

For local backend testing:

```bash
export BACKEND_WS_URL=ws://localhost:8000/runners/connect
```
