from fastapi import APIRouter, status

from app.api.deps import Repository
from app.schemas.auth import AuthRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: AuthRequest, repo: Repository):
    user = repo.create_local_user(payload.email, payload.password)
    return AuthResponse(user_id=user["id"], email=user["email"])


@router.post("/login", response_model=AuthResponse)
def login(payload: AuthRequest, repo: Repository):
    user = repo.verify_local_user(payload.email, payload.password)
    return AuthResponse(user_id=user["id"], email=user["email"])
