from uuid import UUID, uuid4
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.model import User, Post
from app.infrastructure import s3_service, PostMediaUrlCacheService
from app.exceptions import post as post_exc
from app.exceptions import user as user_exc
from app.exceptions import s3_storage as s3_storage_exc
from app.exceptions import redis as redis_exc
from app.schemas import PostCreate, PostUpdate, PostMediaUploadUrl
from app.repository import UnitOfWork
from app.services import post as post_module
from app.utils import hash_password

# --- fixtures ---

@pytest.fixture
async def test_author(
    db_session: AsyncSession
) -> User:
    instance = User(
        username = 'author',
        name = 'author',
        email = 'email@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def test_post(
    db_session: AsyncSession,
    test_author: User
) -> Post:
    instance = Post(
        title = 'title',
        author_id = test_author.user_id,
        content = 'content'
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def test_post_with_media(
    db_session: AsyncSession,
    test_author: User
) -> None:
    instance = Post(
        title = 'title',
        author_id = test_author.user_id,
        content = 'content',
        media_key = f'posts/{test_author.user_id}/'
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

# --- generate_media_upload_url ---

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('data'),
    [
        (PostMediaUploadUrl(content_type = 'image/png')),
        (PostMediaUploadUrl(content_type = 'image/jpeg')),
        (PostMediaUploadUrl(content_type = 'video/mp4')),
        (PostMediaUploadUrl(content_type = 'video/mpeg'))
    ],
    ids = [
        'image/png',
        'image/jpeg',
        'video/mp3',
        'video/mpeg'
    ]
)
async def test_generate_media_upload_url(
    db_session: AsyncSession,
    data: PostMediaUploadUrl,
    test_author: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    generate_presigned_put_url = AsyncMock(return_value = 'upload_url')
    monkeypatch.setattr(s3_service, 'generate_presigned_put_url', generate_presigned_put_url)

    service = post_module.PostService(UnitOfWork(db_session))

    upload_url, key = await service.generate_media_upload_url(test_author.user_id, data)

    assert isinstance(upload_url, str)
    assert isinstance(key, str)
    assert upload_url == 'upload_url'
    generate_presigned_put_url.assert_awaited_once()

# --- create ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_but_author_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.create(uuid4(), PostCreate(
            title = 'title',
            content = 'content'
        ))

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_success(
    db_session: AsyncSession,
    test_author: User
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    post = await service.create(test_author.user_id, PostCreate(
        title = 'title',
        content = 'content'
    ))
    assert isinstance(post, Post)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_with_media_key_success(
    db_session: AsyncSession,
    test_author: User
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    media_key = service._post_prefix(test_author.user_id)
    post = await service.create(
        test_author.user_id,
        PostCreate(
            title = 'title',
            content = 'content',
            media_key = media_key
        )
    )
    assert isinstance(post, Post)
    assert post.media_key == media_key

# --- get_user_posts ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_posts_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.get_user_posts('unknown_user')

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_posts_success(
    db_session: AsyncSession,
    test_author: User,
    test_post: Post
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    posts = await service.get_user_posts(test_author.username)
    assert isinstance(posts, list)
    assert test_post in posts

# --- get ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_post_but_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.get(uuid4(), uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_post_but_post_doesnt_exists(
    db_session: AsyncSession,
    test_author: User
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(post_exc.PostDoesNotExists):
        await service.get(test_author.user_id, uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_post_success(
    db_session: AsyncSession,
    test_author: User,
    test_post: Post
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    post = await service.get(test_author.user_id, test_post.post_id)
    assert post is test_post
    assert isinstance(post, Post)

# --- delete ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_success(
    db_session: AsyncSession,
    test_author: User,
    test_post: Post
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    await service.delete(test_author.user_id, test_post.post_id)
    with pytest.raises(post_exc.PostDoesNotExists):
        await service.get(test_author.user_id, test_post.post_id)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_post_with_media_key_but_s3_internal_error(
    db_session: AsyncSession,
    test_author: User,
    test_post_with_media: Post,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = False)
    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(s3_storage_exc.S3InternalError):
        await service.delete(test_author.user_id, test_post_with_media.post_id)
    delete_object.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_post_with_media_key_but_internal_redis_error(
    db_session: AsyncSession,
    test_author: User,
    test_post_with_media: Post,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = True)
    delete_post_media = AsyncMock(return_value = False)

    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    monkeypatch.setattr(PostMediaUrlCacheService, 'delete_post_media', delete_post_media)

    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.delete(test_author.user_id, test_post_with_media.post_id)
    with pytest.raises(post_exc.PostDoesNotExists):
        await service.get(test_author.user_id, test_post_with_media.post_id)
    delete_object.assert_awaited_once()
    delete_post_media.assert_awaited_once()

# --- update ---

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('title', 'content'),
    [
        ('new_title', None),
        ('new_title', 'new_content'),
        (None, 'new_content')
    ],
    ids = [
        'only_title',
        'all(title and content)',
        'only_content'
    ]
)
async def test_update_success(
    db_session: AsyncSession,
    test_author: User,
    test_post: Post,
    title: str | None,
    content: str | None
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    payload = {
        k: v for k, v in {
            'title' : title,
            'content' : content
        }.items() if v is not None
    }
    updated_post = await service.update(test_author.user_id, test_post.post_id, PostUpdate(**payload))
    assert isinstance(updated_post, Post)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_with_key_rotation_but_s3_internal_error(
    db_session: AsyncSession,
    test_author: User,
    test_post_with_media: Post,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = False)
    monkeypatch.setattr(s3_service, 'delete_object', delete_object)

    service = post_module.PostService(UnitOfWork(db_session))

    with pytest.raises(s3_storage_exc.S3InternalError):
        await service.update(
            test_author.user_id,
            test_post_with_media.post_id,
            PostUpdate(
                title = 'newtitle',
                content = 'newcontent',
                media_key = service._post_prefix(test_author.user_id)
            )
        )
    delete_object.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_with_key_rotation_but_internal_redis_error(
    db_session: AsyncSession,
    test_author: User,
    test_post_with_media: Post,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = True)
    delete_post_media = AsyncMock(return_value = False)

    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    monkeypatch.setattr(PostMediaUrlCacheService, 'delete_post_media', delete_post_media)

    service = post_module.PostService(UnitOfWork(db_session))

    with pytest.raises(redis_exc.InternalRedisError):
        await service.update(
            test_author.user_id,
            test_post_with_media.post_id,
            PostUpdate(
                title = 'newtitle',
                content = 'newcontent',
                media_key = service._post_prefix(test_author.user_id)
            )
        )
    delete_object.assert_awaited_once()
    delete_post_media.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_with_key_rotation_success(
    db_session: AsyncSession,
    test_author: User,
    test_post_with_media: Post,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = True)
    delete_post_media = AsyncMock(return_value = True)

    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    monkeypatch.setattr(PostMediaUrlCacheService, 'delete_post_media', delete_post_media)

    service = post_module.PostService(UnitOfWork(db_session))

    await service.update(
        test_author.user_id,
        test_post_with_media.post_id,
        PostUpdate(
            title = 'newtitle',
            content = 'newcontent',
            media_key = service._post_prefix(test_author.user_id)
        )
    )
    delete_object.assert_awaited_once()
    delete_post_media.assert_awaited_once()

# --- _get_user_and_post ---

@pytest.mark.unit 
@pytest.mark.asyncio
async def test__get_user_and_post_but_user_doesnt_exists(
    db_session: AsyncSession,
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service._get_user_and_post(uuid4(), uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test__get_user_and_post_but_post_doesnt_exists(
    db_session: AsyncSession,
    test_author: User
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(post_exc.PostDoesNotExists):
        await service._get_user_and_post(test_author.user_id, uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test__get_user_and_post_success(
    db_session: AsyncSession,
    test_author: User,
    test_post: Post
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    user, post = await service._get_user_and_post(test_author.user_id, test_post.post_id)
    assert isinstance(user, User)
    assert isinstance(post, Post)
    assert user is test_author
    assert post is test_post

# --- _is_author ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test__is_author_but_user_isnt_author(
    db_session: AsyncSession,
    test_post: Post
) -> None:
    not_author = User(
        username = 'rand_user',
        name = 'rand_user',
        email = 'rand_email@mail.com',
        hashed_password = hash_password('testpass'),
        is_active = True
    )
    db_session.add(not_author)
    await db_session.flush()
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(post_exc.AccessDenied):
        await service._is_author(not_author, test_post)

@pytest.mark.unit
@pytest.mark.asyncio
async def test__is_author_success(
    db_session: AsyncSession,
    test_author: User,
    test_post: Post
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    await service._is_author(test_author, test_post)

# --- _validate_post_key ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test__validate_post_key_but_invalid_media_key(
    db_session: AsyncSession,
    test_author: User
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    with pytest.raises(post_exc.InvalidMediaKey):
        service._validate_post_key(test_author.user_id, 'invalid-key')

@pytest.mark.unit
@pytest.mark.asyncio
async def test__validate_post_key_success(
    db_session: AsyncMock,
    test_author: User
) -> None:
    service = post_module.PostService(UnitOfWork(db_session))
    service._validate_post_key(test_author.user_id, service._post_prefix(test_author.user_id))
