from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch

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
from app.exceptions import verification_token as verification_exc
from app.utils import hash_password
from app.infrastructure import LoginCodeServiceReturnValues, LoginCodeService
from app.infrastructure import TokenServiceReturnValues, TokenService
from app.infrastructure import VerificationTokenService, VerificationTokenServiceReturnValues


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

# --- logout ---

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('status', 'excepted_exc'),
    [
        (TokenServiceReturnValues.ERROR, redis_exc.InternalRedisError),
        (TokenServiceReturnValues.NOT_FOUND, auth_exc.TokenNotFoundError)
    ],
    ids = ['internal_redis_error', 'not_found_error']
)
async def test_logout_with_errors(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    excepted_exc: HTTPException
) -> None:
    delete_refresh_token = AsyncMock(return_value = status)
    monkeypatch.setattr(TokenService, 'delete_refresh_token', delete_refresh_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(excepted_exc):
        await service.logout(active_user.user_id)
    delete_refresh_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_logout_success(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    monkeypatch.setattr(TokenService, 'delete_refresh_token', delete_refresh_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    res = await service.logout(active_user.user_id)
    assert res is None
    delete_refresh_token.assert_awaited_once()

# --- verify email ---

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('status', 'excepted_exc'),
    [
        (VerificationTokenServiceReturnValues.ERROR, redis_exc.InternalRedisError),
        (VerificationTokenServiceReturnValues.NOT_FOUND, verification_exc.VerificationTokenNotFoundError),
        (VerificationTokenServiceReturnValues.NOT_EQUAL, verification_exc.VerificationTokenNotEqualError)
    ],
    ids = ['internal_redis_error', 'not_found', 'not_equal']
)
async def test_verify_email_with_first_errors(
    db_session: AsyncSession,
    active_user: User, 
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    excepted_exc: HTTPException
) -> None:
    check_verification_token = AsyncMock(return_value = status)
    monkeypatch.setattr(VerificationTokenService, 'check_verification_token', check_verification_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(excepted_exc):
        await service.verify_email(active_user.user_id, '1234')
    check_verification_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_email_but_user_does_not_exists(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    check_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    monkeypatch.setattr(VerificationTokenService, 'check_verification_token', check_verification_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.verify_email(uuid4(), '1234')
    check_verification_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_email_but_user_is_active(
    db_session: AsyncSession, 
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    check_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    monkeypatch.setattr(VerificationTokenService, 'check_verification_token', check_verification_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    res = await service.verify_email(active_user.user_id, '1234')
    assert isinstance(res, User)
    check_verification_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_email_but_user_is_not_active_and_internal_redis_error(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    active_user.is_active = False
    await db_session.flush()
    check_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    delete_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.ERROR)
    monkeypatch.setattr(VerificationTokenService, 'check_verification_token', check_verification_token)
    monkeypatch.setattr(VerificationTokenService, 'delete_verification_token', delete_verification_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.verify_email(active_user.user_id, '1234')
    check_verification_token.assert_awaited_once()
    delete_verification_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_verify_success(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    active_user.is_active = False
    await db_session.flush()
    check_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    delete_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    monkeypatch.setattr(VerificationTokenService, 'check_verification_token', check_verification_token)
    monkeypatch.setattr(VerificationTokenService, 'delete_verification_token', delete_verification_token)
    service = auth_module.AuthService(UnitOfWork(db_session))
    res = await service.verify_email(active_user.user_id, '1234')
    assert isinstance(res, User)
    check_verification_token.assert_awaited_once()
    delete_verification_token.assert_awaited_once()

# --- refresh ---

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('value', 'excepted_exc'),
    [
        (None, auth_exc.InvalidTokenError),
        ({'token': '1234'}, auth_exc.InvalidTokenError)
    ],
    ids = ['payload_is_none', 'payload_hasnt_sub']
)
async def test_refresh_but_payload_errors(
    db_session: AsyncSession,
    value: str | None,
    excepted_exc: HTTPException
) -> None:
    decode_refresh_token = Mock(return_value = value)
    service = auth_module.AuthService(UnitOfWork(db_session))
    with patch.object(auth_module, 'decode_refresh_token', decode_refresh_token):
        with pytest.raises(excepted_exc):
            await service.refresh('bad-token')
    decode_refresh_token.assert_called_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('user_exists', 'is_active', 'status', 'excepted_exc'),
    [
        (False, None,  TokenServiceReturnValues.ERROR,   redis_exc.InternalRedisError),
        (False, None,  TokenServiceReturnValues.SUCCESS, auth_exc.UserNotActive),
        (True,  False, TokenServiceReturnValues.ERROR,   redis_exc.InternalRedisError),
        (True,  False, TokenServiceReturnValues.SUCCESS, auth_exc.UserNotActive)
    ],
    ids = [
        'user_doesnt_exists_redis_error',
        'user_doesnt_exists_redis_success',
        'user_exists_but_not_active_redis_error',
        'user_exists_but_not_active_redis_success'
    ]
)
async def test_refresh_but_user_doesnt_exists_or_not_active(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch,
    user_exists: bool,
    is_active: bool | None,
    status: int, 
    excepted_exc: HTTPException
) -> None:
    if user_exists:
        active_user.is_active = is_active
        await db_session.flush()
        user_id = active_user.user_id
    else:
        user_id = uuid4()
    decode_refresh_token = Mock(return_value = {'sub': str(user_id)})
    delete_refresh_token = AsyncMock(return_value = status)

    monkeypatch.setattr(auth_module, 'decode_refresh_token', decode_refresh_token)
    monkeypatch.setattr(TokenService, 'delete_refresh_token', delete_refresh_token)

    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(excepted_exc):
        await service.refresh('refresh-token')
    decode_refresh_token.assert_called_once_with('refresh-token')
    delete_refresh_token.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('status', 'excepted_exc'),
    [
        (TokenServiceReturnValues.ERROR, redis_exc.InternalRedisError),
        (TokenServiceReturnValues.SUCCESS, auth_exc.TokenInBlacklistError)
    ],
    ids = [
        'internal_redis_error',
        'token_in_blacklist_error'
    ]
)
async def test_refresh_in_blacklist_with_errors(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    excepted_exc: HTTPException
) -> None:
    decode_refresh_token = Mock(return_value = {'sub': str(active_user.user_id)})
    in_blacklist = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    delete_refresh_token = AsyncMock(return_value = status)

    monkeypatch.setattr(auth_module, 'decode_refresh_token', decode_refresh_token)
    monkeypatch.setattr(TokenService, 'in_blacklist', in_blacklist)
    monkeypatch.setattr(TokenService, 'delete_refresh_token', delete_refresh_token)

    service = auth_module.AuthService(UnitOfWork(db_session))

    with pytest.raises(excepted_exc):
        await service.refresh('refresh-token')
    in_blacklist.assert_awaited_once_with('refresh-token')
    delete_refresh_token.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('stored', 'status_deleted', 'excepted_exc'),
    [
        (TokenServiceReturnValues.ERROR, TokenServiceReturnValues.SUCCESS, redis_exc.InternalRedisError),
        (TokenServiceReturnValues.NOT_FOUND, TokenServiceReturnValues.SUCCESS, auth_exc.TokenNotFoundError),
        ('another-token', TokenServiceReturnValues.ERROR, redis_exc.InternalRedisError),
        ('another-token', TokenServiceReturnValues.SUCCESS, auth_exc.DifferentTokensError)
    ],
    ids = [
        'stored_error',
        'stored_not_found',
        'another_token_and_redis_error',
        'another_token'
    ]
)
async def test_refresh_stored_with_errors(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch,
    stored: int,
    status_deleted: int,
    excepted_exc: HTTPException
) -> None:
    decode_refresh_token = Mock(return_value = {'sub': str(active_user.user_id)})
    in_blacklist = AsyncMock(return_value = TokenServiceReturnValues.NOT_FOUND)
    get_refresh_token = AsyncMock(return_value = stored)
    delete_refresh_token = AsyncMock(return_value = status_deleted)

    monkeypatch.setattr(auth_module, 'decode_refresh_token', decode_refresh_token)
    monkeypatch.setattr(TokenService, 'in_blacklist', in_blacklist)
    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    monkeypatch.setattr(TokenService, 'delete_refresh_token', delete_refresh_token)

    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(excepted_exc):
        await service.refresh('refresh-token')
    in_blacklist.assert_awaited_once_with('refresh-token')
    get_refresh_token.assert_awaited_once()
    delete_refresh_token.assert_awaited_once() if stored == 'another-token' else None

@pytest.mark.asyncio
async def test_refresh_but_add_old_token_to_blacklist_error(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    decode_refresh_token = Mock(return_value = {'sub': str(active_user.user_id)})
    in_blacklist = AsyncMock(return_value = TokenServiceReturnValues.NOT_FOUND)
    get_refresh_token = AsyncMock(return_value = 'refresh-token')
    add_to_blacklist = AsyncMock(return_value = TokenServiceReturnValues.ERROR)
    
    monkeypatch.setattr(auth_module, 'decode_refresh_token', decode_refresh_token)
    monkeypatch.setattr(TokenService, 'in_blacklist', in_blacklist)
    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    monkeypatch.setattr(TokenService, 'add_to_blacklist', add_to_blacklist)

    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.refresh('refresh-token')
    in_blacklist.assert_awaited_once_with('refresh-token')
    get_refresh_token.assert_awaited_once()
    add_to_blacklist.assert_awaited_once()

@pytest.mark.asyncio
async def test_refresh_success_but_store_new_refresh_token_error(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    decode_refresh_token = Mock(return_value = {'sub': str(active_user.user_id)})
    in_blacklist = AsyncMock(return_value = TokenServiceReturnValues.NOT_FOUND)
    get_refresh_token = AsyncMock(return_value = 'refresh-token')
    add_to_blacklist = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    store_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.ERROR)
    
    monkeypatch.setattr(auth_module, 'decode_refresh_token', decode_refresh_token)
    monkeypatch.setattr(TokenService, 'in_blacklist', in_blacklist)
    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    monkeypatch.setattr(TokenService, 'add_to_blacklist', add_to_blacklist)
    monkeypatch.setattr(TokenService, 'store_refresh_token', store_refresh_token)

    service = auth_module.AuthService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.refresh('refresh-token')
    in_blacklist.assert_awaited_once_with('refresh-token')
    get_refresh_token.assert_awaited_once()
    add_to_blacklist.assert_awaited_once()
    store_refresh_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_refresh_success(
    db_session: AsyncSession,
    active_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    decode_refresh_token = Mock(return_value = {'sub': str(active_user.user_id)})
    in_blacklist = AsyncMock(return_value = TokenServiceReturnValues.NOT_FOUND)
    get_refresh_token = AsyncMock(return_value = 'refresh-token')
    add_to_blacklist = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    store_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    
    monkeypatch.setattr(auth_module, 'decode_refresh_token', decode_refresh_token)
    monkeypatch.setattr(TokenService, 'in_blacklist', in_blacklist)
    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    monkeypatch.setattr(TokenService, 'add_to_blacklist', add_to_blacklist)
    monkeypatch.setattr(TokenService, 'store_refresh_token', store_refresh_token)

    service = auth_module.AuthService(UnitOfWork(db_session))
    res = await service.refresh('refresh-token')
    assert isinstance(res, TokenResponse)
    in_blacklist.assert_awaited_once_with('refresh-token')
    get_refresh_token.assert_awaited_once()
    add_to_blacklist.assert_awaited_once()
    store_refresh_token.assert_awaited_once()
