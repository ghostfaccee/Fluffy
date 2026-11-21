from uuid import UUID, uuid4

from app.core import yaml_settings
from app.infrastructure import s3_service, PostMediaUrlCacheService
from app.repository import UnitOfWork
from app.schemas import PostCreate, PostUpdate, PostMediaUploadUrl
from app.exceptions import user as user_exc
from app.exceptions import post as post_exc
from app.exceptions import s3_storage as s3_storage_exc
from app.exceptions import redis as redis_exc
from app.model import Post, User

class PostService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow
    
    # --- crud ---

    async def generate_media_upload_url(self, user_id: UUID, data: PostMediaUploadUrl) -> tuple[str, str]:
        content_type = data.content_type
        if content_type.startswith('image'):
            extension = 'jpg' if content_type == 'image/jpeg' else 'png'
        elif content_type.startswith('video'):
            extension = 'mp4' if content_type == 'video/mp4' else 'mpeg'
        key = f'{self._post_prefix(user_id)}{uuid4()}.{extension}'
        upload_url = await s3_service.generate_presigned_put_url(key, content_type, yaml_settings.POST_MEDIA_PRESIGNED_PUT_URL_LIFETINE_MINUTES * 60)
        return upload_url, key
    
    async def create(self, author_id: UUID, data: PostCreate) -> Post:
        author = await self.uow.user.get(author_id)
        if author is None:
            raise user_exc.UserDoesNotExists()
        if data.media_key is not None:
            self._validate_post_key(author_id, data.media_key)
        post = Post(
            author_id = author_id,
            title = data.title,
            content = data.content,
            media_key = data.media_key
        )
        post.author = author
        self.uow.post.add(post)
        await self.uow.commit()
        return post
    
    async def get_user_posts(self, username: str, limit: int = 20, offset: int = 0) -> list[Post]:
        author = await self.uow.user.get_by_username(username)
        if author is None:
            raise user_exc.UserDoesNotExists()
        return await self.uow.post.get_user_posts(author.user_id, limit, offset)
    
    async def get(self, user_id: UUID, post_id: UUID) -> Post:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        # It doesn’t matter to us at all which user it is; the main thing is that they exist.
        post = await self.uow.post.get_with_author(post_id)
        if post is None:
            raise post_exc.PostDoesNotExists()
        return post
    
    async def delete(self, user_id: UUID, post_id: UUID) -> None:
        user, post = await self._get_user_and_post(user_id, post_id)
        await self._is_author(user, post)
        presense_of_key = post.media_key
        if presense_of_key:
            deleted = await s3_service.delete_object(post.media_key)
            if not deleted:
                raise s3_storage_exc.S3InternalError()
        await self.uow.post.delete(post)
        await self.uow.commit()
        if presense_of_key:
            deleted = await PostMediaUrlCacheService.delete_post_media(post.media_key)
            if not deleted:
                raise redis_exc.InternalRedisError()
    
    async def update(self, user_id: UUID, post_id: UUID, data: PostUpdate) -> Post:
        user, post = await self._get_user_and_post(user_id, post_id)
        await self._is_author(user, post)
        update_data = data.model_dump(exclude_unset = True)
        old_key = post.media_key
        key_rotation = 'media_key' in update_data and old_key
        if key_rotation:
            if update_data.get('media_key') is not None:
                self._validate_post_key(user_id, data.media_key)
            deleted = await s3_service.delete_object(old_key)
            if not deleted:
                raise s3_storage_exc.S3InternalError()
        for key, value in update_data.items():
            setattr(post, key, value)
        post.author = user
        await self.uow.commit()
        if key_rotation:
            deleted = await PostMediaUrlCacheService.delete_post_media(old_key)
            if not deleted:
                raise redis_exc.InternalRedisError()
        return post
    
    # --- helpers ---
    
    async def _get_user_and_post(self, user_id: UUID, post_id: UUID) -> tuple[User, Post]:
        user = await self.uow.user.get(user_id)
        if user is None:
            raise user_exc.UserDoesNotExists()
        post = await self.uow.post.get(post_id)
        if post is None:
            raise post_exc.PostDoesNotExists()
        return user, post

    async def _is_author(self, user: User, post: Post) -> None:
        if user.user_id != post.author_id:
            raise post_exc.AccessDenied()

    def _post_prefix(self, author_id: UUID) -> str:
        return f'{yaml_settings.POST_MEDIA_KEY}{author_id}/'
    
    def _validate_post_key(self, author_id: UUID, key: str) -> None:
        prefix = self._post_prefix(author_id)
        if not key.startswith(prefix):
            raise post_exc.InvalidMediaKey()
