import asyncio
import json
from uuid import UUID, uuid4
from typing import Any
from collections.abc import Callable
from functools import wraps, partial


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
    async def get_or_set(
        cls,
        key: str,
        factory: Callable,
        ttl: int | None = None,
        lock_timeout: int = 10,
        wait_timeout: int = 2,
        wait_interval: float = 0.05
    ) -> Any:
        '''
        Get value from cache or compute it via factory with thundering herd protection.
        Only one caller computes the value; others wait for it to appear in cache.
        args:
            * key - cache key
            * factory - async callable that computes the value on cache miss
            * ttl - lifetime (in seconds)
            * lock_timeout - how long the lock lives (should exceed max factory time)
            * wait_timeout - how long waiters poll before falling back
            * wait_interval - poll interval for waiters
        '''
        if not cls._enabled:
            return await factory()

        cached = await cls.get(key)
        if cached is not None:
            return cached

        redis = await RedisClient.get_client()
        lock_key = f'lock:{key}'
        token = uuid4().hex
        got_lock = await redis.set(lock_key, token, nx=True, ex=lock_timeout)

        if got_lock:
            try:
                cached = await cls.get(key)
                if cached is not None:
                    return cached
                res = await factory()
                if res is not None:
                    await cls.set(key, res, ttl)
                return res
            finally:
                await cls._unlock(redis, lock_key, token)

        # Lock is held by someone else — wait for the winner to populate the cache
        loop = asyncio.get_running_loop()
        deadline = loop.time() + wait_timeout
        while loop.time() < deadline:
            await asyncio.sleep(wait_interval)
            cached = await cls.get(key)
            if cached is not None:
                return cached

        # Still nothing: try to take the lock once more without waiting
        token = uuid4().hex
        got_lock = await redis.set(lock_key, token, nx=True, ex=lock_timeout)
        if got_lock:
            try:
                cached = await cls.get(key)
                if cached is not None:
                    return cached
                res = await factory()
                if res is not None:
                    await cls.set(key, res, ttl)
                return res
            finally:
                await cls._unlock(redis, lock_key, token)

        # Could not take the lock — serve without caching rather than stampede
        logger.warning(f'Cache lock wait timeout for key={key}, serving without cache')
        return await factory()
    
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
            return result > 0
        except Exception as e:
            logger.error(f'Cache delete error: {e}')
            return False

    @classmethod
    async def delete_by_pattern(cls, pattern: str) -> int:
        '''
        Delete data by pattern
        '''
        if not cls._enabled:
            return 0
        try:
            redis = await RedisClient.get_client()
            deleted = 0
            async for key in redis.scan_iter(match = pattern, count = 200):
                deleted += await redis.delete(key)
            logger.info(f'Cache deleted {deleted} keys by pattern={pattern}')
            return deleted
        except Exception as e:
            logger.error(f'Cache delete by pattern error: {e}')
            return 0
    
    @classmethod
    def cached(
        cls, 
        ttl: int | None = None, 
        namespace: str = '', 
        user_id_field: str = '', 
        extra_fields: list | None = None,
        use_lock: bool = False,
        lock_timeout: int = 10,
        wait_timeout: int = 2
    ) -> Callable:
        '''
        Decorator for function caching
        args: 
            * ttl - lifetime (in seconds)
            * namespace - namespace (for groupings)
            * user_id_field - the argument name containing user_id; if not specified, it uses a shared cache for all users. Always use user_id_field for authorized endpoints.
            * extra_fields - a list of names of additional arguments required to be added to the key. This is perfect for endpoints with parameters (for example: extra_fields = ['username'] for the endpoint /v1/users/{username})
            * use_lock - Designed to address herd-related issues. Disabled by default; should be enabled for demanding tasks.
            * lock_timeout - lock lifetime
            * wait_timeout - time for waiters to poll the cache
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
                if use_lock:
                    return await cls.get_or_set(
                        key,
                        factory = partial(func, *args, **kwargs),
                        ttl = ttl,
                        lock_timeout = lock_timeout,
                        wait_timeout = wait_timeout
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

    @staticmethod
    async def _unlock(redis, lock_key: str, token: str) -> None:
        '''
        Atomically release the lock only if it still belongs to us.
        '''
        lua = '''
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        '''
        try:
            await redis.eval(lua, 1, lock_key, token)
        except Exception as e:
            logger.error(f'Cache unlock error: {e}')