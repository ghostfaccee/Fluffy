import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model import User

@pytest.mark.integration
async def test_db_session_user_real_async_session(db_session: AsyncSession) -> None:
    assert await db_session.execute(select(User.user_id).limit(1)) is not None
