from uuid import UUID
from typing import Optional

from app.core import RedisClient, logger, yaml_settings
from app.infrastructure.storage import s3_avatars

class GroupAvatarUrlCacheService:
    AVATAR_URL_PREFIX = 'group_avatar_url'

    @classmethod
    def _avatar_url_key(cls, group_id: UUID) -> str:
        return f'{cls.AVATAR_URL_PREFIX}:{group_id}'
    
    @classmethod
    async def get_avatar(cls, group_id: UUID, avatar_key: str) -> Optional[str]:
        try:
            redis = await RedisClient.get_client()
            key = cls._avatar_url_key(group_id)
            stored_url = await redis.get(key)
            if stored_url:
                return stored_url
            presigned_url = await s3_avatars.generate_presigned_get_url(avatar_key)
            await redis.set(key, presigned_url, ex = yaml_settings.AVATAR_URL_CACHE_LIFETIME_MINUTES * 60)
            return presigned_url
        except Exception as e:
            logger.error(f'Failed to get avatar: {e}')
            return None
    
    @classmethod
    async def delete_avatar(cls, group_id: UUID) -> bool:
        try:
            redis = await RedisClient.get_client()
            key = cls._avatar_url_key(group_id)
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f'Faileed to delete avatar: {e}')
            return False
    