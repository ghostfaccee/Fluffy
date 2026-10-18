from uuid import uuid4
from unittest.mock import AsyncMock, Mock, ANY

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services import auth as auth_module
from app.schemas import UserLoginRequest, LoginVerifyRequest, TokenResponse
from app.repository import UnitOfWork
from app.model import User
from app.exceptions import auth as auth_exc
from app.exceptions import redis as redis_exc
from app.exceptions import user as user_exc
from app.utils import hash_password
from app.infrastructure import LoginCodeServiceReturnValues, LoginCodeService
from app.infrastructure import TokenServiceReturnValues, TokenService


# --- fixtures ---

@pytest_asyncio.fixture
async def active_user(db_session: AsyncSession) -> User:
    suffix = uuid4().hex
    instance = User(
        username = f'user_{suffix[:10]}',
        name = 'testuser',
        email = f'randomemail_{suffix[:10]}@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

# --- login tests ---

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('username', 'password', 'active', 'excepted_exc'),
    [
        ('anotheruser', 'testpass', True, auth_exc.InvalidCredentials),
        (None, 'another_testpass', True, auth_exc.InvalidCredentials),
        (None, 'testpass', False, auth_exc.UserNotActive)
    ],
    ids = ['another_username', 'another_password', 'user_is_not_active']
)
async def test_login_errors(
    db_session: AsyncSession, 
    active_user: User, 
    monkeypatch: pytest.MonkeyPatch, 
    username: str | None, 
    password: str, 
    active: bool, 
    excepted_exc: HTTPException
) -> None:
    active_user.is_active = active
    await db_session.flush()

    store_code = AsyncMock(
        return_value = LoginCodeServiceReturnValues.SUCCESS
    )
    monkeypatch.setattr(LoginCodeService, "store_code", store_code)

    username = username or active_user.username
    service = auth_module.AuthService(UnitOfWork(db_session))

    with pytest.raises(excepted_exc):
        await service.login(
            UserLoginRequest(
                username=username,
                password=password,
            )
        )

    store_code.assert_not_awaited()
    # Verification: whether or not the test invoked a mock.

@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession, active_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    store_code = AsyncMock(return_value = LoginCodeServiceReturnValues.SUCCESS)
    send_code = Mock()

    monkeypatch.setattr(LoginCodeService, 'store_code', store_code)
    monkeypatch.setattr(auth_module.send_code, 'delay', send_code)

    service = auth_module.AuthService(UnitOfWork(db_session))

    res = await service.login(
        UserLoginRequest(
            username = active_user.username,
            password = 'testpass'
        )
    )

    assert res is None
    store_code.assert_awaited_once()

@pytest.mark.asyncio
async def test_login_excepted_redis_error(db_session: AsyncSession, active_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    store_code = AsyncMock(return_value = LoginCodeServiceReturnValues.ERROR)
    monkeypatch.setattr(LoginCodeService, 'store_code', store_code)
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.login(
            UserLoginRequest(
                username = active_user.username,
                password = 'testpass'
            )
        )
    store_code.assert_awaited_once()

# --- verification login code ---

@pytest.mark.asyncio
async def test_login_verification_code_but_user_does_not_exists(db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch) -> None:
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.verify_login_code(
            LoginVerifyRequest(code = '1234'),
            username = 'unknown_user'
        )

@pytest.mark.asyncio
async def test_login_verification_code_but_user_is_not_active(db_session: AsyncSession, active_user: User, monkeypatch: pytest.MonkeyPatch) -> None:
    active_user.is_active = False
    await db_session.flush()
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(auth_exc.UserNotActive):
        await service.verify_login_code(
            LoginVerifyRequest(code = '1234'),
            username = active_user.username
        )

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('status', 'excepted_exc'),
    [
        (LoginCodeServiceReturnValues.ERROR, redis_exc.InternalRedisError),
        (LoginCodeServiceReturnValues.NOT_EQUAL, auth_exc.LoginCodeIsNotEqual),
        (LoginCodeServiceReturnValues.NOT_FOUND, auth_exc.LoginCodeNotFound)
    ],
    ids = ['redis_error', 'login_code_is_not_equal', 'login_code_not_found']
)
async def test_verify_login_code_check_first_status(
    db_session: AsyncSession, 
    active_user: User, 
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    excepted_exc: HTTPException
) -> None:
    check_code = AsyncMock(return_value = status)
    monkeypatch.setattr(LoginCodeService, 'check_code', check_code)

    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(excepted_exc):
        await service.verify_login_code(
            LoginVerifyRequest(code = '1234'),
            username = active_user.username
        )
    check_code.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_login_code_success_but_internal_redis_error_while_deleting(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    check_code = AsyncMock(return_value = LoginCodeServiceReturnValues.SUCCESS)
    delete_code = AsyncMock(return_value = LoginCodeServiceReturnValues.ERROR)

    monkeypatch.setattr(LoginCodeService, 'check_code', check_code)
    monkeypatch.setattr(LoginCodeService, 'delete_code', delete_code)

    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.verify_login_code(
            LoginVerifyRequest(code = '1234'),
            username = active_user.username
        )
    check_code.assert_awaited_once()
    delete_code.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_login_code_success_but_internal_redis_error_while_store_refresh_token(
    db_session: AsyncSession, 
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    check_code = AsyncMock(return_value = LoginCodeServiceReturnValues.SUCCESS)
    delete_code = AsyncMock(return_value = LoginCodeServiceReturnValues.SUCCESS)
    store_refresh = AsyncMock(return_value = TokenServiceReturnValues.ERROR)

    monkeypatch.setattr(LoginCodeService, 'check_code', check_code)
    monkeypatch.setattr(LoginCodeService, 'delete_code', delete_code)
    monkeypatch.setattr(TokenService, 'store_refresh_token', store_refresh)

    service = auth_module.AuthService(UnitOfWork(db_session))

    with pytest.raises(redis_exc.InternalRedisError):
        await service.verify_login_code(
            LoginVerifyRequest(code = '1234'),
            username = active_user.username
        )
    check_code.assert_awaited_once()
    delete_code.assert_awaited_once()
    store_refresh.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_login_code_success(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    check_code = AsyncMock(return_value = LoginCodeServiceReturnValues.SUCCESS)
    delete_code = AsyncMock(return_value = LoginCodeServiceReturnValues.SUCCESS)
    store_refresh = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)

    monkeypatch.setattr(LoginCodeService, 'check_code', check_code)
    monkeypatch.setattr(LoginCodeService, 'delete_code', delete_code)
    monkeypatch.setattr(TokenService, 'store_refresh_token', store_refresh)

    service = auth_module.AuthService(UnitOfWork(db_session))

    resp = await service.verify_login_code(
        LoginVerifyRequest(code = '1234'),
        username = active_user.username
    )

    assert isinstance(resp, TokenResponse)
    assert resp.access_token is not None
    assert resp.refresh_token is not None
    check_code.assert_awaited_once()
    delete_code.assert_awaited_once()
    store_refresh.assert_awaited_once()

# --- ---