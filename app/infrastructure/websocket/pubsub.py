import asyncio
import json
from uuid import UUID

from app.core import RedisClient, logger
from app.infrastructure.websocket.manager import manager

class PubSubService:
    WS_CHANNEL_PREFIX = 'ws:user'

    @classmethod
    def _channel(cls, user_id: UUID) -> str:
        return f'{cls.WS_CHANNEL_PREFIX}:{user_id}'
    
    @classmethod
    async def publish_to_user(cls, user_id: UUID, message: dict) -> None:
        redis = await RedisClient.get_client()
        await redis.publish(cls._channel(user_id), json.dumps(message))
    
    @classmethod
    async def listen_ws_channel(cls) -> None:
        redis = await RedisClient.get_client()
        pubsub = redis.pubsub()
        await pubsub.psubscribe(f'{cls.WS_CHANNEL_PREFIX}:*')
        logger.info('WS pubsub listener started')
        try:
            async for msg in pubsub.listen():
                if msg['type'] != 'pmessage':
                    continue
                try:
                    channel = msg['channel']
                    user_id = channel[len(cls.WS_CHANNEL_PREFIX)+1:]
                    user_id = UUID(user_id)
                    payload = msg['data']
                    message = json.loads(payload)
                    await manager.send_to_local(user_id, message)
                except Exception as e:
                    logger.error(f'WS pubsub message failed: {e}')
        except asyncio.CancelledError:
            logger.info('WS pubsub listener cancelled')
            raise
        finally:
            await pubsub.punsubscribe(f'{cls.WS_CHANNEL_PREFIX}:*')
            await pubsub.close()

async def listen_ws_channel_with_reconnect() -> None:
    while True:
        try:
            await PubSubService.listen_ws_channel()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f'WS listener died: {e}. Reconnect in 5s...')
            await asyncio.sleep(5)
