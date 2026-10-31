
import json
from uuid import UUID
from typing import Any
from collections.abc import Callable
from functools import wraps


from app.core import logger, RedisClient, yaml_settings

class CachingService:
    _enabled = True

    @classmethod
    def disable(cls) -> None:
        '''
        Disable cache for tests
        '''
        cls._enabled = False
        logger.info('[!] Cache disabled')
    
    @classmethod
    def enable(cls) -> None:
        '''
        Enable cache for work
        '''
        cls._enabled = True
        logger.info('[!] Cache enabled')

    @classmethod
    def _make_key(
        cls,
        func_name: str,
        namespace: str = '',
        user_id: UUID | None = None,
        extra: dict | None = None
    ) -> str:
        '''
        Generates a unique key for cache
        '''
        key = f'{namespace}:{func_name}' if namespace else func_name
        if user_id is not None:
            key += f':user_{user_id}'
        if extra:
            for extra_key, extra_value in sorted(extra.items()):
                key += f':{extra_key}_{extra_value}'
        return key
    
    @classmethod
    async def get(cls, key: str) -> Any | None:
        '''
        Retrieve data from the cache using a key
        '''
        if not cls._enabled:
            return None
        try:
            redis = await RedisClient.get_client()
            data = await redis.get(key)
            if data is None:
                return None
            try:
                return json.loads(data)
            except:
                return data
        except Exception as e:
            logger.error(f'Cache get error: {e}')
            return None
    
    @classmethod
    async def set(cls, key: str, value: Any, ttl: int | None = None) -> bool:
        '''
        Save data to the cache
        '''
        if not cls._enabled:
            return False
        try:
            redis = await RedisClient.get_client()
            if hasattr(value, 'model_dump'):
                data = json.dumps(value.model_dump(), default = str)
            else:
                try:
                    data = json.dumps(value)
                except:
                    data = str(value)
            ttl = ttl or yaml_settings.CACHING_DEFAULT_TTL
            await redis.set(key, data, ex = ttl)
            return True
        except Exception as e:
            logger.error(f'Cache set error: {e}')
            return False
    
    @classmethod
    async def delete(cls, key: str) -> bool:
        '''
        Delete data by key
        '''
        if not cls._enabled:
            return False
        try:
            redis = await RedisClient.get_client()
            result = await redis.delete(key)
            return result >= 0
        except Exception as e:
            logger.error(f'Cache delete error: {e}')
            return False
    
    @classmethod
    async def cached(
        cls, 
        ttl: int | None = None, 
        namespace: str = '', 
        user_id_field: str = '', 
        extra_fields: list | None = None
    ) -> Callable:
        '''
        Decorator for function caching
        args: 
            * ttl - lifetime (in seconds)
            * namespace - namespace (for groupings)
            * user_id_field - the argument name containing user_id; if not specified, it uses a shared cache for all users. Always use user_id_field for authorized endpoints.
            * extra_fields - a list of names of additional arguments required to be added to the key. This is perfect for endpoints with parameters (for example: extra_fields = ['username'] for the endpoint /v1/users/{username})
        '''
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not cls._enabled:
                    return await func(*args, **kwargs)
                user_id = None
                if user_id_field and user_id_field in kwargs:
                    user_id = kwargs[user_id_field]
                extra = {}
                if extra_fields:
                    for ex_field in extra_fields:
                        if ex_field in kwargs:
                            extra[ex_field] = kwargs[ex_field]
                key = cls._make_key(
                    func_name = func.__name__,
                    namespace = namespace,
                    user_id = user_id,
                    extra = extra
                )
                cached_data = await cls.get(key)
                if cached_data is not None:
                    return cached_data
                res = await func(*args, **kwargs)
                if res is not None:
                    await cls.set(key, res, ttl)
                return res
            return wrapper
        return decorator