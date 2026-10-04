import hashlib
from uuid import UUID
from typing import Optional
from enum import IntEnum

from app.core import RedisClient, logger, yaml_settings

class TokenServiceReturnValues(IntEnum):
    ERROR = -1
    NOT_FOUND = 0
    SUCCESS = 1

class TokenService:
    REFRESH_PREFIX = 'refresh'
    BLACKLIST_PREFIX = 'blacklist'

    @classmethod
    def _hash_token(cls, token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @classmethod
    def _refresh_key(cls, user_id: UUID) -> str:
        return f'{cls.REFRESH_PREFIX}:{user_id}'
    
    @classmethod
    def _blacklist_key(cls, token: str) -> str:
        return f'{cls.BLACKLIST_PREFIX}:{cls._hash_token(token)}'
    
    @classmethod
    async def store_refresh_token(cls, user_id: UUID, refresh_token: str, ttl: int = yaml_settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400) -> TokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._refresh_key(user_id)
            await redis.set(key, refresh_token, ex = ttl)
            return TokenServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to store refresh token: {e}')
            return TokenServiceReturnValues.ERROR
    
    @classmethod
    async def get_refresh_token(cls, user_id: UUID) -> str | TokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._refresh_key(user_id)
            refresh_token = await redis.get(key)
            if refresh_token is None:
                return TokenServiceReturnValues.NOT_FOUND
            return refresh_token
        except Exception as e:
            logger.error(f'Failed to get refresh token: {e}')
            return TokenServiceReturnValues.ERROR
    
    @classmethod
    async def delete_refresh_token(cls, user_id: UUID) -> TokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._refresh_key(user_id)
            deleted = await redis.delete(key)
            if deleted == 0:
                return TokenServiceReturnValues.NOT_FOUND
            return TokenServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to delete refresh token: {e}')
            return TokenServiceReturnValues.ERROR
    
    @classmethod
    async def add_to_blacklist(cls, token: str, ttl: int = yaml_settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400) -> TokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._blacklist_key(token)
            await redis.set(key, '1', ex = ttl)
            return TokenServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to add token to blacklist: {e}')
            return TokenServiceReturnValues.ERROR
    
    @classmethod
    async def in_blacklist(cls, token: str) -> TokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._blacklist_key(token)
            is_found = await redis.get(key)
            if is_found is None:
                return TokenServiceReturnValues.NOT_FOUND
            return TokenServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to find token in blacklist: {e}')
            return TokenServiceReturnValues.ERROR
