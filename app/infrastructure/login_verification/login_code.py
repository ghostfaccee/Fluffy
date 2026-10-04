import hashlib
import hmac
from uuid import UUID
from typing import Optional
from enum import IntEnum

from app.core import RedisClient, logger, yaml_settings

class LoginCodeServiceReturnValues(IntEnum):
    ERROR = -1
    NOT_FOUND = 0
    SUCCESS = 1
    NOT_EQUAL = 2

class LoginCodeService:
    LOGIN_CODE_PREFIX = 'login_code'

    @classmethod
    def _hash_code(cls, code: str) -> str:
        return hashlib.sha256(code.encode('utf-8')).hexdigest()
    
    @classmethod
    def _login_code_key(cls, user_id: UUID) -> str:
        return f'{cls.LOGIN_CODE_PREFIX}:{user_id}'
    
    @classmethod
    async def store_code(cls, user_id: UUID, code: str, ttl: int = yaml_settings.LOGIN_CODE_EXPIRE_MINUTES * 60) -> LoginCodeServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._login_code_key(user_id)
            code = cls._hash_code(code)
            await redis.set(key, code, ex = ttl)
            return LoginCodeServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to store login code: {e}')
            return LoginCodeServiceReturnValues.ERROR

    @classmethod
    async def check_code(cls, user_id: UUID, plain_code: str) -> LoginCodeServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._login_code_key(user_id)
            stored_hash = await redis.get(key)
            if stored_hash is None:
                return LoginCodeServiceReturnValues.NOT_FOUND
            plain_code = cls._hash_code(plain_code)
            if hmac.compare_digest(plain_code, stored_hash):
                return LoginCodeServiceReturnValues.SUCCESS
            else:
                return LoginCodeServiceReturnValues.NOT_EQUAL
        except Exception as e:
            logger.error(f'Failed to check login code: {e}')
            return LoginCodeServiceReturnValues.ERROR
    
    @classmethod
    async def delete_code(cls, user_id: UUID) -> LoginCodeServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._login_code_key(user_id)
            deleted = await redis.delete(key)
            if deleted == 0:
                return LoginCodeServiceReturnValues.NOT_FOUND
            return LoginCodeServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to delete login code: {e}')
            return LoginCodeServiceReturnValues.ERROR
