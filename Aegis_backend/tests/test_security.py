import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import get_current_user


@pytest.mark.asyncio
async def test_missing_session_is_rejected():
    with pytest.raises(HTTPException) as exc:
        await get_current_user(None, Settings())

    assert exc.value.status_code == 401
