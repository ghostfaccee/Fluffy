from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.model import User, Story
from app.schemas import StoryUploadRequest, StoryCreate
from app.utils import hash_password
from app.infrastructure import s3_service, StoryMediaUrlCacheService
from app.repository import UnitOfWork
from app.services import story as story_module
from app.exceptions import user as user_exc
from app.exceptions import story as story_exc
from app.exceptions import s3_storage as s3_storage_exc
from app.exceptions import redis as redis_exc

# --- fixtures ---

@pytest.fixture
async def test_story_author(
    db_session: AsyncSession
) -> User:
    instance = User(
        username = 'storyteller',
        name = 'storyteller',
        email = 'storyteller@mail.com',
        hashed_password = hash_password('123'),
        is_active = True
    )
    db_session.add(instance)
    await db_session.flush()
    return instance

@pytest.fixture
async def test_story_with_author(
    db_session: AsyncSession,
    test_story_author: User
) -> Story:
    instance = Story(
        title = 'title',
        media_key = 'media_key',
        author_id = test_story_author.user_id
    )
    instance.author = test_story_author
    db_session.add(instance)
    await db_session.flush()
    return instance

# --- generate_story_upload_url ---

@pytest.mark.unit
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ('data'),
    [
        (StoryUploadRequest(content_type = 'image/png')),
        (StoryUploadRequest(content_type = 'image/jpeg')),
        (StoryUploadRequest(content_type = 'video/mp4')),
        (StoryUploadRequest(content_type = 'video/mpeg'))
    ],
    ids = [
        'image/png',
        'image/jpeg',
        'video/mp3',
        'video/mpeg'
    ]
)
async def test_generate_story_upload_url_for_image(
    db_session: AsyncSession,
    data: StoryUploadRequest,
    test_story_author: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    generate_presigned_put_url = AsyncMock(return_value = 'upload_url')
    monkeypatch.setattr(s3_service, 'generate_presigned_put_url', generate_presigned_put_url)

    service = story_module.StoryService(UnitOfWork(db_session))

    upload_url, key = await service.generate_story_upload_url(test_story_author.user_id, data)

    assert isinstance(upload_url, str)
    assert isinstance(key, str)
    assert upload_url == 'upload_url'
    generate_presigned_put_url.assert_awaited_once()

# --- create ---

@pytest.mark.unit
@pytest.mark.asyncio
async def create_story_but_author_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.create(
            uuid4(),
            StoryCreate(
                title = 'title',
                media_key = 'media-key'
            )
        )

@pytest.mark.unit
@pytest.mark.asyncio
async def create_story_but_story_limit_exceed(
    db_session: AsyncSession,
    test_story_author: User,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    get_count_of_user_active_stories = AsyncMock(return_vlaue = 5)
    monkeypatch.setattr(story_module.StoryService.uow.story, 'get_count_of_user_active_stories', get_count_of_user_active_stories)

    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(story_exc.StoryLimitExceeded):
        await service.create(
            test_story_author.user_id,
            StoryCreate(
                title = 'title',
                media_key = 'media_key'
            )
        )

@pytest.mark.unit
@pytest.mark.asyncio
async def create_story_success(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    story = await service.create(
        test_story_author.user_id,
        StoryCreate(
            title = 'title',
            media_key = 'media_key'
        )
    )
    assert isinstance(story, Story)

# --- get_user_stories ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_stories_but_request_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.get_user_stories(uuid4(), 'username')

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_stories_but_user_doesnt_exists(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.get_user_stories(test_story_author.user_id, 'username')

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_stories_success(
    db_session: AsyncSession,
    test_story_author: User,
    test_story_with_author: Story
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    stories = await service.get_user_stories(test_story_author.user_id, test_story_with_author.author.username)
    assert isinstance(stories, list)
    assert len(stories) == 1

# --- get_active_story_by_id ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_story_by_id_but_request_user_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.get_active_story_by_id(uuid4(), uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_story_but_story_doesnt_exists(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(story_exc.StoryDoesNotExists):
        await service.get_active_story_by_id(test_story_author.user_id, uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_story_success(
    db_session: AsyncSession,
    test_story_author: User,
    test_story_with_author: Story
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    story = await service.get_active_story_by_id(test_story_author.user_id, test_story_with_author.story_id)
    assert isinstance(story, Story)

# --- get_all_author_stories ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_author_stories_but_author_doesnt_exists(
    db_session: AsyncSession
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service.get_all_author_stories(uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_all_author_stories_success(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    stories = await service.get_all_author_stories(test_story_author.user_id)
    assert isinstance(stories, list)
    assert len(stories) == 0

# --- get_author_story ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_author_story_success(
    db_session: AsyncSession,
    test_story_author: User,
    test_story_with_author: Story
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    story = await service.get_author_story(test_story_author.user_id, test_story_with_author.story_id)
    assert isinstance(story, Story)

# --- delete ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_but_s3_internal_error(
    db_session: AsyncMock,
    test_story_author: User,
    test_story_with_author: Story,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = False)
    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(s3_storage_exc.S3InternalError):
        await service.delete(test_story_author.user_id, test_story_with_author.story_id)
    delete_object.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_but_internal_redis_error(
    db_session: AsyncSession,
    test_story_author: User,
    test_story_with_author: Story,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = True)
    delete_story_media = AsyncMock(return_value = False)

    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    monkeypatch.setattr(StoryMediaUrlCacheService, 'delete_story_media', delete_story_media)

    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(redis_exc.InternalRedisError):
        await service.delete(test_story_author.user_id, test_story_with_author.story_id)
    with pytest.raises(story_exc.StoryDoesNotExists):
        await service.get_author_story(test_story_author.user_id, test_story_with_author.story_id)
    delete_object.assert_awaited_once()
    delete_story_media.assert_awaited_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_success(
    db_session: AsyncSession,
    test_story_author: User,
    test_story_with_author: Story,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    delete_object = AsyncMock(return_value = True)
    delete_story_media = AsyncMock(return_value = True)

    monkeypatch.setattr(s3_service, 'delete_object', delete_object)
    monkeypatch.setattr(StoryMediaUrlCacheService, 'delete_story_media', delete_story_media)

    service = story_module.StoryService(UnitOfWork(db_session))
    await service.delete(test_story_author.user_id, test_story_with_author.story_id)
    with pytest.raises(story_exc.StoryDoesNotExists):
        await service.get_author_story(test_story_author.user_id, test_story_with_author.story_id)
    delete_object.assert_awaited_once()
    delete_story_media.assert_awaited_once()

# --- _get_user_and_story ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test__get_user_and_story_but_user_doesnt_exists(
    db_session: AsyncSession,
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(user_exc.UserDoesNotExists):
        await service._get_user_and_story(uuid4(), uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test__get_user_and_story_but_story_doesnt_exists(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(story_exc.StoryDoesNotExists):
        await service._get_user_and_story(test_story_author.user_id, uuid4())

@pytest.mark.unit
@pytest.mark.asyncio
async def test__get_user_and_story_but_story_doesnt_exists(
    db_session: AsyncSession,
    test_story_author: User,
    test_story_with_author: Story
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    user, story = await service._get_user_and_story(test_story_author.user_id, test_story_with_author.story_id)
    assert isinstance(user, User)
    assert isinstance(story, Story)

# --- _is_author ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test__is_author_but_user_doesnt_author_of_story(
    db_session: AsyncSession,
    test_story_with_author: Story
) -> None:
    not_author = User(
        username = 'not_author',
        name = 'NotAuthor',
        email = 'not_author@mail.com',
        hashed_password = hash_password('123'),
        is_active = True
    )
    db_session.add(not_author)
    await db_session.flush()
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(story_exc.AccessDenied):
        await service._is_author(not_author, test_story_with_author)

@pytest.mark.unit
@pytest.mark.asyncio
async def test__is_author_success(
    db_session: AsyncSession, 
    test_story_author: User,
    test_story_with_author: Story
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    service._is_author(test_story_author, test_story_with_author)

# --- _validate_story_key ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test__validate_story_key_but_invalid_story_key(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    with pytest.raises(story_exc.InvalidStoryKey):
        service._validate_story_key(test_story_author.user_id, 'key')

@pytest.mark.unit
@pytest.mark.asyncio
async def test__validate_story_key_success(
    db_session: AsyncSession,
    test_story_author: User
) -> None:
    service = story_module.StoryService(UnitOfWork(db_session))
    key = f'{service._story_prefix(test_story_author.user_id)}/user'
    service._validate_story_key(test_story_author.user_id, key)
