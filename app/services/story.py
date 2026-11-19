from uuid import UUID, uuid4

from app.model import Story, User
from app.repository import UnitOfWork
from app.schemas import StoryCreate, StoryUploadRequest
from app.core import yaml_settings
from app.exceptions import story as story_exc
from app.exceptions import user as user_exc
from app.infrastructure import s3_service

class StoryService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
    
    async def generate_story_upload_url(
        self,
        user_id: UUID,
        data: StoryUploadRequest
    ) -> tuple[str, str]:
        content_type = data.content_type
        if content_type.startswith('image'):
            extension = 'jpg' if content_type == 'image/jpeg' else 'png'
        elif content_type.startswith('video'):
            extension = 'mp4' if content_type == 'video/mp4' else 'mpeg'
        key = f'{self._story_prefix(user_id)}{uuid4()}.{extension}'
        upload_url = await s3_service.generate_presigned_put_url(key, content_type, yaml_settings.STORY_PRESIGNED_PUT_URL_LIFETIME_MINUTES * 60)
        return upload_url, key

    async def create(self, author_id: UUID, data: StoryCreate) -> Story:
        author = await self.uow.user.get(author_id)
        if author is None:
            raise user_exc.UserDoesNotExists()
        count = await self.uow.story.get_count_of_user_active_stories(author_id)
        if count >= 5:
            raise story_exc.StoryLimitExceeded()
        self._validate_story_key(author_id, data.media_key)
        story = Story(
            title = data.title,
            media_key = data.media_key,
            author_id = author_id
        )
        story.author = author
        self.uow.story.add(story)
        await self.uow.commit()
        return story
    
    async def get_user_stories(self, request_user_id: UUID, username: str) -> list[Story]:
        if await self.uow.user.get(request_user_id) is None:
            raise user_exc.UserDoesNotExists()
        user = await self.uow.user.get_by_username(username)
        if user is None:
            raise user_exc.UserDoesNotExists()
        return await self.uow.story.get_active_stories_by_author_id(user.user_id)
    
    async def get_active_story_by_id(self, request_user_id: UUID, story_id: UUID) -> Story:
        if await self.uow.user.get(request_user_id) is None:
            raise user_exc.UserDoesNotExists()
        story = await self.uow.story.get_active_by_id(story_id)
        if story is None:
            raise story_exc.StoryDoesNotExists()
        return story
    
    async def get_all_author_stories(self, author_id: UUID) -> list[Story]:
        author = await self.uow.user.get(author_id)
        if author is None:
            raise user_exc.UserDoesNotExists()
        return await self.uow.story.get_all_stories_by_author_id(author_id)
    
    async def get_author_story(self, author_id: UUID, story_id: UUID) -> Story:
        author, story = await self._get_user_and_story(author_id, story_id)
        self._is_author(author, story)
        return story
    
    async def delete(self, author_id: UUID, story_id: UUID) -> None:
        author, story = await self._get_user_and_story(author_id, story_id)
        self._is_author(author, story)
        await self.uow.story.delete(story)
        await self.uow.commit()

    async def _get_user_and_story(self, user_id: UUID, story_id: UUID) -> tuple[User, Story]:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        story = await self.uow.story.get_story(story_id)
        if story is None:
            raise story_exc.StoryDoesNotExists()
        return user, story
    
    def _is_author(self, user: User, story: Story) -> None:
        if user.user_id != story.author_id:
            raise story_exc.AccessDenied()

    def _story_prefix(self, user_id: UUID) -> str:
        return f'{yaml_settings.STORY_KEY}{user_id}/'

    def _validate_story_key(self, user_id: UUID, key: str) -> None:
        prefix = f'{self._story_prefix(user_id)}'
        if not key.startswith(prefix):
            raise story_exc.InvalidStoryKey()
