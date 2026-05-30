from fastapi import APIRouter, WebSocket, status

from app.core.config import get_settings
from app.rag.runner_manager import runner_manager

router = APIRouter(prefix="/runners", tags=["runners"])


@router.websocket("/connect")
async def connect_runner(websocket: WebSocket):
    settings = get_settings()
    supplied_secret = websocket.headers.get("x-runner-secret") or websocket.query_params.get("token")
    if not settings.runner_shared_secret or supplied_secret != settings.runner_shared_secret:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid runner secret.")
        return

    await runner_manager.connect(websocket)
