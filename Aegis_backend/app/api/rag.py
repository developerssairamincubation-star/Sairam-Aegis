from fastapi import APIRouter

from app.api.deps import Rag
from app.schemas.rag import RagStatus

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/status", response_model=RagStatus)
def rag_status(rag: Rag):
    return rag.status()
