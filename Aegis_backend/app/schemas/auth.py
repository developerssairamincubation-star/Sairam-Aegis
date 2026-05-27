from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    user_id: str
    email: str


class AuthUser(BaseModel):
    id: str
    email: str | None = None
    raw: dict
