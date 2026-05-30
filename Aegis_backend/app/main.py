from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chats, projects, rag, runners
from app.core.config import get_settings
from app.db.supabase import get_repository
from app.rag.service import get_rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.rag_ingest_on_startup:
        rag_service = get_rag_service()
        ingestion = rag_service.ingest_on_startup()
        get_repository().record_ingestion_run(
            indexed_files=ingestion.indexed_files,
            indexed_chunks=ingestion.indexed_chunks,
            status_value="completed",
        )
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name}


app.include_router(projects.router)
app.include_router(chats.router)
app.include_router(rag.router)
app.include_router(auth.router)
app.include_router(runners.router)
