from typing import Annotated

from fastapi import Depends, HTTPException, Query, status

from app.db.supabase import SupabaseRepository, get_repository
from app.rag.service import RagService, get_rag_service


def get_user_id(user_id: str | None = Query(default=None)) -> str:
	if not user_id:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user_id.")
	return user_id


UserId = Annotated[str, Depends(get_user_id)]
Repository = Annotated[SupabaseRepository, Depends(get_repository)]
Rag = Annotated[RagService, Depends(get_rag_service)]
