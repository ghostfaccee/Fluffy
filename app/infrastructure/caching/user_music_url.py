from uuid import UUID

from app.core import RedisClient, yaml_settings, logger
from app.infrastructure import s3_service

class UserMusicCacheService:
    MUSIC_URL_PREFIX = 'user_music_url'

    @classmethod
    def _music_url_key(cls, user_id: UUID) -> str:
        return f'{cls.MUSIC_URL_PREFIX}:{user_id}'
    
    @classmethod
    async def get_music(cls, user_id: UUID, music_key: str) -> str | None:
        try:
            redis = await RedisClient.get_client()
            key = cls._music_url_key(user_id)
            stored_url = await redis.get(key)
            if stored_url:
                return stored_url
            presigned_url = await s3_service.generate_presigned_get_url(music_key, yaml_settings.USER_MUSIC_PRESIGNED_GET_URL_LIFETIME_MINUTES * 60)
            await redis.set(key, presigned_url, ex = yaml_settings.USER_MUSIC_CACHE_LIFETIME_MINUTES * 60)
            return presigned_url
        except Exception as e:
            logger.error(f'Failed to get music url: {e}')
            return None

    @classmethod
    async def delete_music(cls, user_id: UUID) -> bool:
        try:
            redis = await RedisClient.get_client()
            key = cls._music_url_key(user_id)
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f'Failed to delete music url: {e}')
            return False
