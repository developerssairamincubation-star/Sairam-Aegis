from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)


class ProjectOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
