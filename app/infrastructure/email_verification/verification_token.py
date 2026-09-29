import hashlib
import hmac
from uuid import UUID
from typing import Optional
from enum import IntEnum

from app.core import RedisClient, logger, yaml_settings

class VerificationTokenServiceReturnValues(IntEnum):
    ERROR = -1
    NOT_FOUND = 0
    SUCCESS = 1
    NOT_EQUAL = 2

class VerificationTokenService:
    VERIFICATION_PREFIX = 'verification_token'

    @classmethod
    def _hash_verification_token(cls, token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    @classmethod
    def _verification_token_key(cls, user_id: UUID) -> str:
        return f'{cls.VERIFICATION_PREFIX}:{user_id}'
    
    @classmethod
    async def store_verification_token(cls, user_id: UUID, token: str, ttl: int = yaml_settings.VERIFICATION_TOKEN_EXPIRE_MINUTES * 60) -> VerificationTokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._verification_token_key(user_id)
            token = cls._hash_verification_token(token)
            await redis.set(key, token, ex = ttl)
            return VerificationTokenServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to store verification token: {e}')
            return VerificationTokenServiceReturnValues.ERROR
    
    @classmethod
    async def check_verification_token(cls, user_id: UUID, plain_token: str) -> VerificationTokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._verification_token_key(user_id)
            stored_hash = await redis.get(key)
            if stored_hash is None:
                return VerificationTokenServiceReturnValues.NOT_FOUND
            plain_token = cls._hash_verification_token(plain_token)
            if hmac.compare_digest(plain_token, stored_hash):
                return VerificationTokenServiceReturnValues.SUCCESS
            else:
                return VerificationTokenServiceReturnValues.NOT_EQUAL
        except Exception as e:
            logger.error(f'Failed to check verification token: {e}')
            return VerificationTokenServiceReturnValues.ERROR
    
    @classmethod
    async def delete_verification_token(cls, user_id: UUID) -> VerificationTokenServiceReturnValues:
        try:
            redis = await RedisClient.get_client()
            key = cls._verification_token_key(user_id)
            deleted = await redis.delete(key)
            if deleted == 0:
                return TokenServiceReturnValues.NOT_FOUND
            return TokenServiceReturnValues.SUCCESS
        except Exception as e:
            logger.error(f'Failed to delete verification token: {e}')
            return VerificationTokenServiceReturnValues.ERROR
