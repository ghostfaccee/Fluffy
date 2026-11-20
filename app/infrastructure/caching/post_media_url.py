import hashlib

from app.core import RedisClient, logger, yaml_settings
from app.infrastructure import s3_service

class PostMediaUrlCacheService:
    POST_MEDIA_PREFIX = 'post_media_url'

    @classmethod
    def _post_media_hashed_prefix(cls, media_key: str) -> str:
        digest = hashlib.sha256(media_key.encode()).hexdigest()
        return f'{cls.POST_MEDIA_PREFIX}:{digest}'
    
    @classmethod
    async def get_post_media_url(cls, post_media_key: str) -> str | None:
        try:
            redis = await RedisClient.get_client()
            key = cls._post_media_hashed_prefix(post_media_key)
            stored_url = await redis.get(key)
            if stored_url:
                return stored_url
            presigned_url = await s3_service.generate_presigned_get_url(post_media_key, yaml_settings.POST_MEDIA_PRESIGNED_GET_URL_LIFETIME_MINUTES * 60)
            await redis.set(key, presigned_url, ex = yaml_settings.POST_MEDIA_CACHE_LIFETIME_MINUTES * 60)
            return presigned_url
        except Exception as e:
            logger.error(f'Failed to get post media url: {e}')
            return None
    
    @classmethod
    async def delete_post_media(cls, post_media_key: str) -> bool:
        try:
            redis = await RedisClient.get_client()
            key = cls._post_media_hashed_prefix(post_media_key)
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f'Failed to delete post media url: {e}')
            return False
