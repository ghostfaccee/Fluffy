from uuid import UUID
from typing import Optional

from app.core import RedisClient, yaml_settings, logger
from app.infrastructure.storage import s3_service

class AvatarUrlCacheService:
    AVATAR_URL_PREFIX = 'avatar_url'

    @classmethod
    def _avatar_url_key(cls, user_id: UUID) -> str:
        return f'{cls.AVATAR_URL_PREFIX}:{user_id}'
    
    @classmethod
    async def get_avatar(cls, user_id: UUID, avatar_key: str) -> Optional[str]:
        try:
            redis = await RedisClient.get_client()
            key = cls._avatar_url_key(user_id)
            stored_url = await redis.get(key)
            if stored_url:
                return stored_url
            presigned_url = await s3_service.generate_presigned_get_url(avatar_key, yaml_settings.AVATAR_PRESIGNED_GET_URL_LIFETIME_MINUTES * 60)
            await redis.set(key, presigned_url, ex = yaml_settings.AVATAR_URL_CACHE_LIFETIME_MINUTES * 60)
            return presigned_url
        except Exception as e:
            logger.error(f'Failed to get avatar url: {e}')
            return None

    @classmethod
    async def delete_avatar(cls, user_id: UUID) -> bool:
        try:
            redis = await RedisClient.get_client()
            key = cls._avatar_url_key(user_id)
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f'Failed to delete avatar url: {e}')
            return False
