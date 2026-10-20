import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from unittest.mock import AsyncMock, Mock

from app.services import user as user_module
from app.model import User
from app.repository import UnitOfWork
from app.utils import hash_password
from app.exceptions import user as user_exc
from app.exceptions import redis as redis_exc
from app.schemas import UserRegister
from app.infrastructure import VerificationTokenServiceReturnValues, VerificationTokenService

# --- fixtures --- 

@pytest.fixture
async def existing_user(db_session: AsyncSession) -> User:
    instance = User(
        username = f'existing_user',
        name = 'testuser',
        email = f'email@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

# --- create ---
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('username', 'email', 'excepted_exc'),
    [
        ('existing_user', 'another_email@mail.com', user_exc.UsernameAlreadyTaken),
        ('another_user', 'email@mail.com', user_exc.EmailAlreadyTaken),
        ('existing_user', 'email@mail.com', user_exc.UsernameAlreadyTaken),
    ]
)
async def test_create_but_integrity_errors(
    db_session: AsyncSession,
    existing_user: User,
    username: str,
    email: str,
    excepted_exc: HTTPException
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(excepted_exc):
        await service.create(UserRegister(
            name = 'testuser',
            username = username,
            email = email,
            password = 'testpass'
        ))

@pytest.mark.asyncio
async def test_create_but_internal_redis_error(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    store_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.ERROR)
    monkeypatch.setattr(VerificationTokenService, 'store_verification_token', store_verification_token)
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.create(UserRegister(
            name = 'testuser',
            username = 'username',
            email = 'email@mail.com',
            password = 'testpass'
        ))
    store_verification_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_success(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    store_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    send_token = Mock()

    monkeypatch.setattr(VerificationTokenService, 'store_verification_token', store_verification_token)
    monkeypatch.setattr(user_module.send_verification_email, 'delay', send_token)

    service = user_module.UserService(UnitOfWork(db_session))

    res = await service.create(
        UserRegister(
            name = 'testuser',
            username = 'username',
            email = 'email@mail.com',
            password = 'testpass'
        )
    )
    assert isinstance(res, User)
    store_verification_token.assert_awaited_once()
    send_token.assert_called_once()
