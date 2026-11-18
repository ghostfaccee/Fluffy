import hashlib

from app.core import RedisClient, logger, yaml_settings
from app.infrastructure import s3_service

class StoryMediaUrlCacheService:
    STORY_PREFIX = 'story_media_url'
    
    @classmethod
    def _story_hashed_prefix(cls, media_key: str) -> str:
        digest = hashlib.sha256(media_key.encode()).hexdigest()
        return f'{cls.STORY_PREFIX}:{digest}'
    
    @classmethod
    async def get_story_media(cls, story_media_key: str) -> str | None:
        try:
            redis = await RedisClient.get_client()
            key = cls._story_hashed_prefix(story_media_key)
            stored_url = await redis.get(key)
            if stored_url:
                return stored_url
            presigned_url = await s3_service.generate_presigned_get_url(story_media_key, yaml_settings.STORY_PRESIGNED_GET_URL_LIFETIME_MINUTES * 60)
            await redis.set(key, presigned_url, ex = yaml_settings.STORY_CACHE_LIFETIME_MINUTES * 60)
            return presigned_url
        except Exception as e:
            logger.error(f'Failed to get story url: {e}')
            return None
    
    @classmethod
    async def delete_story_media(cls, story_media_key: str) -> bool:
        try:
            redis = await RedisClient.get_client()
            key = cls._story_hashed_prefix(story_media_key)
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f'Failed to delete story url: {e}')
            return False
