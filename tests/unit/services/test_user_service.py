import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from app.services import user as user_module
from app.model import User
from app.repository import UnitOfWork
from app.utils import hash_password
from app.exceptions import user as user_exc
from app.exceptions import redis as redis_exc
from app.exceptions import s3_storage as s3_storage_exc
from app.schemas import UserRegister, UserUpdate, PasswordUpdate
from app.infrastructure import VerificationTokenServiceReturnValues, VerificationTokenService
from app.infrastructure import TokenService, TokenServiceReturnValues, s3_avatars
from app.infrastructure import AvatarUrlCacheService

# --- fixtures --- 

@pytest.fixture
async def existing_user(db_session: AsyncSession) -> User:
    instance = User(
        username = 'existing_user',
        name = 'testuser',
        email = 'email@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def existing_user_2(db_session: AsyncSession) -> User:
    instance = User(
        username = 'existing_user2',
        name = 'testuser2',
        email = 'email2@mail.com',
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

# --- get ---

@pytest.mark.asyncio
async def test_get_user_but_user_doesnt_exists(
    db_session: AsyncSession,
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    res = await service.get(uuid4())
    assert res is None

@pytest.mark.asyncio 
async def test_get_user_success(
    db_session: AsyncSession,
    existing_user: User
) -> None:
    await db_session.commit()
    service = user_module.UserService(UnitOfWork(db_session))
    res = await service.get(existing_user.user_id)
    assert isinstance(res, User)

# --- get by username ---

@pytest.mark.asyncio
async def test_get_by_username_but_user_doesnt_exists(
    db_session: AsyncSession,
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    res = await service.get_by_username('testuser')
    assert res is None

@pytest.mark.asyncio
async def test_get_by_username_success(
    db_session: AsyncSession,
    existing_user: User
) -> None:
    await db_session.commit()
    service = user_module.UserService(UnitOfWork(db_session))
    res = await service.get_by_username(existing_user.username)
    assert isinstance(res, User)

# --- update ---

@pytest.mark.asyncio
async def test_update_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.update(uuid4(), UserUpdate())

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('username', 'email', 'excepted_exc'),
    [
        ('existing_user', 'email@mail.com', user_exc.UsernameAlreadyTaken),
        ('existing_user', 'new_email@mail.com', user_exc.UsernameAlreadyTaken),
        ('new_username', 'email@mail.com', user_exc.EmailAlreadyTaken)
    ],
    ids = [
        'all (username and email)',
        'only_username',
        'only_email'
    ]
)
async def test_update_but_integrity_errors(
    db_session: AsyncSession,
    existing_user: User,
    existing_user_2: User,
    username: str,
    email: str,
    excepted_exc: HTTPException
) -> None:
    await db_session.commit()
    service = user_module.UserService(UnitOfWork(db_session))
    data = UserUpdate(
        username = username,
        email = email
    )
    with pytest.raises(excepted_exc):
        await service.update(existing_user_2.user_id, data)

@pytest.mark.asyncio
async def test_update_but_internal_redis_error_is_store_verification_token(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    await db_session.commit()
    store_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.ERROR)
    monkeypatch.setattr(VerificationTokenService, 'store_verification_token', store_verification_token)

    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.update(existing_user.user_id, UserUpdate(email = 'new@mail.com'))
    store_verification_token.assert_awaited_once()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('name', 'username', 'email', 'bio', 'city', 'university', 'institute', 'group', 'values'),
    [
        ('new_name', None, None, None, None, None, None, None, 1),
        ('new_name', 'new_username', None, None, None, None, None, None, 2),
        ('new_name', 'new_username', 'new_email@mail.com', None, None, None, None, None, 3),
        ('new_name', 'new_username', 'new_email@mail.com', 'new_bio', None, None, None, None, 4),
        ('new_name', 'new_username', 'new_email@mail.com', 'new_bio', 'new_city', None, None, None, 5),
        ('new_name', 'new_username', 'new_email@mail.com', 'new_bio', 'new_city', 'new_university', None, None, 6),
        ('new_name', 'new_username', 'new_email@mail.com', 'new_bio', 'new_city', 'new_university', 'new_institute', 'new_group', 7),
        ('new_name', 'new_username', 'new_email@mail.com', 'new_bio', 'new_city', 'new_university', 'new_institute', 'new_grpup', 8),
    ],
    ids = [
        'only_name',
        'name & username',
        'name & username & email',
        'name & username & email & bio',
        'name & username & email & bio & city',
        'name & username & email & bio & city & university',
        'name & username & email & bio & city & university & istitute',
        'all'
    ]
)
async def test_update_user_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    username: str,
    email: str,
    bio: str,
    city: str,
    university: str,
    institute: str,
    group: str,
    values: int
) -> None:
    store_verification_token = AsyncMock(return_value = VerificationTokenServiceReturnValues.SUCCESS)
    send_verification_email = Mock()
    invalidate_token = AsyncMock(return_value = True)

    monkeypatch.setattr(VerificationTokenService, 'store_verification_token', store_verification_token)
    monkeypatch.setattr(user_module.send_verification_email, 'delay', send_verification_email)
    monkeypatch.setattr(user_module.UserService, '_invalidate_token', invalidate_token)

    service = user_module.UserService(UnitOfWork(db_session))

    payload = {
        k: v for k, v in {
            'name': name,
            'username': username,
            'email': email,
            'bio': bio,
            'city': city,
            'university': university,
            'institute': institute,
            'group': group,
        }.items() if v is not None
    }

    res = await service.update(
        existing_user.user_id,
        UserUpdate(**payload)
    )

    assert isinstance(res, User)
    if values >= 3:
        store_verification_token.assert_awaited_once()
        send_verification_email.assert_called_once()
        invalidate_token.assert_awaited_once()

# --- generate avatar upload url ---

@pytest.mark.asyncio
async def test_generate_avatar_upload_url_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    generate_presigned_put_url = AsyncMock(return_value = 'upload-url')
    monkeypatch.setattr(s3_avatars, 'generate_presigned_put_url', generate_presigned_put_url)

    service = user_module.UserService(UnitOfWork(db_session))

    upload_url, key = await service.generate_avatar_upload_url(existing_user.user_id, 'png')

    assert isinstance(upload_url, str) and upload_url == 'upload-url'
    assert isinstance(key, str)
    generate_presigned_put_url.assert_awaited_once()

# --- set avatar ---

@pytest.mark.asyncio
async def test_set_avatar_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.set_avatar(uuid4(), 'key')

@pytest.mark.asyncio
async def test_set_avatar_but_delete_avatar__from_redis_error(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = False)

    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)

    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(redis_exc.InternalRedisError):
        await service.set_avatar(existing_user.user_id, 'key')
    delete_avatar.assert_awaited_once()

@pytest.mark.asyncio
async def test_set_avatar_but_delete_avatar_from_s3_error(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    existing_user.avatar_key = 'key'
    await db_session.commit()

    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = False)

    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(s3_storage_exc.S3InternalError):
        await service.set_avatar(existing_user.user_id, 'key')
    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

@pytest.mark.asyncio
async def test_set_avatar_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    existing_user.avatar_key = 'key'
    await db_session.commit()

    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = True)

    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = user_module.UserService(UnitOfWork(db_session))

    res = await service.set_avatar(existing_user.user_id, 'key')

    assert isinstance(res, User)
    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

# --- delete avatar ---

@pytest.mark.asyncio
async def test_delete_avatar_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.delete_avatar(uuid4())

@pytest.mark.asyncio
async def test_delete_avatar_but_internal_redis_error_while_deleting_avatar(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = False)

    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)

    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(redis_exc.InternalRedisError):
        await service.delete_avatar(existing_user.user_id)
    delete_avatar.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_avatar_but_s3_internal_error_while_deleting_object(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    existing_user.avatar_key = 'key'
    await db_session.commit()

    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = False)

    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(s3_storage_exc.S3InternalError):
        await service.delete_avatar(existing_user.user_id)
    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_avatar_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    existing_user.avatar_key = 'key'
    await db_session.commit()

    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = True)

    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = user_module.UserService(UnitOfWork(db_session))

    await service.delete_avatar(existing_user.user_id)

    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

# --- update password ---

@pytest.mark.asyncio
async def test_update_password_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.update_password(uuid4(), PasswordUpdate(
            old_password = '1234',
            new_password = '1234'
        ))

@pytest.mark.asyncio
async def test_update_password_but_invalid_password(
    db_session: AsyncSession,
    existing_user: User
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(user_exc.InvalidPassword):
        await service.update_password(existing_user.user_id, PasswordUpdate(
            old_password = 'testpassX',
            new_password = '12345'
        ))

@pytest.mark.asyncio
async def test_update_password_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    invalidate_token = AsyncMock(return_value = True)
    monkeypatch.setattr(user_module.UserService, '_invalidate_token', invalidate_token)

    service = user_module.UserService(UnitOfWork(db_session))

    res = await service.update_password(
        existing_user.user_id,
        PasswordUpdate(
            old_password = 'testpass',
            new_password = '1234'
        )
    )

    assert isinstance(res, User)
    invalidate_token.assert_awaited_once()


# --- delete ---

@pytest.mark.asyncio
async def test_delete_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(user_exc.UserDoesNotExists):
        await service.delete(uuid4())

@pytest.mark.asyncio
async def test_delete_but_internal_redis_error_while_delete_avatar(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_avatar = AsyncMock(return_value = False)
    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)

    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(redis_exc.InternalRedisError):
        await service.delete(existing_user.user_id)
    delete_avatar.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_but_internal_s3_error_while_delete_object(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    existing_user.avatar_key = 'key'
    await db_session.commit()

    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = False)
    
    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(s3_storage_exc.S3InternalError):
        await service.delete(existing_user.user_id)
    
    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

@pytest.mark.asyncio
async def test_delete_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    existing_user.avatar_key = 'key'
    await db_session.commit()

    delete_avatar = AsyncMock(return_value = True)
    delete_object = AsyncMock(return_value = True)
    
    monkeypatch.setattr(AvatarUrlCacheService, 'delete_avatar', delete_avatar)
    monkeypatch.setattr(s3_avatars, 'delete_object', delete_object)

    service = user_module.UserService(UnitOfWork(db_session))

    await service.delete(existing_user.user_id)
    
    delete_avatar.assert_awaited_once()
    delete_object.assert_awaited_once()

# --- invalidate token ---

@pytest.mark.asyncio
async def test_invalidate_token_but_internal_redis_error_while_get(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    get_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.ERROR)
    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    
    service = user_module.UserService(UnitOfWork(db_session))

    with pytest.raises(redis_exc.InternalRedisError):
        await service._invalidate_token(existing_user.user_id)
    get_refresh_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_invalidate_token_but_token_not_found(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    get_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.NOT_FOUND)
    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    
    service = user_module.UserService(UnitOfWork(db_session))

    res = await service._invalidate_token(existing_user.user_id)

    assert isinstance(res, bool)
    assert not res
    get_refresh_token.assert_awaited_once()

@pytest.mark.asyncio
async def test_invalidate_token_but_internal_redis_error_while_add_to_blacklist(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    get_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    add_to_blacklist = AsyncMock(return_value = TokenServiceReturnValues.ERROR)

    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    monkeypatch.setattr(TokenService, 'add_to_blacklist', add_to_blacklist)

    service = user_module.UserService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service._invalidate_token(existing_user.user_id)
    get_refresh_token.assert_awaited_once()
    add_to_blacklist.assert_awaited_once()

@pytest.mark.asyncio
async def test_invalidate_token_success(
    db_session: AsyncSession,
    existing_user: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    get_refresh_token = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)
    add_to_blacklist = AsyncMock(return_value = TokenServiceReturnValues.SUCCESS)

    monkeypatch.setattr(TokenService, 'get_refresh_token', get_refresh_token)
    monkeypatch.setattr(TokenService, 'add_to_blacklist', add_to_blacklist)

    service = user_module.UserService(UnitOfWork(db_session))

    res = await service._invalidate_token(existing_user.user_id)

    assert isinstance(res, bool)
    assert res
    get_refresh_token.assert_awaited_once()
    add_to_blacklist.assert_awaited_once()