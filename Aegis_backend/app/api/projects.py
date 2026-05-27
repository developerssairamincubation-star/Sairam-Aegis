from fastapi import APIRouter, Response, status

from app.api.deps import Repository, UserId
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(user_id: UserId, repo: Repository):
    return repo.list_projects(user_id)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, user_id: UserId, repo: Repository):
    return repo.create_project(user_id, payload.model_dump())


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, payload: ProjectUpdate, user_id: UserId, repo: Repository):
    return repo.update_project(user_id, project_id, payload.model_dump())


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, user_id: UserId, repo: Repository):
    repo.delete_project(user_id, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
