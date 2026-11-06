import asyncio

from app.core import logger
from app.infrastructure.websocket.manager import manager

async def cleanup_stale_connections() -> None:
    while True:
        try:
            await asyncio.sleep(30)
            stale = manager.get_stale_connections()
            for user_id, ws in stale:
                logger.warning(f'WS stale, user: {user_id}. Closing...')
                try:
                    await ws.close()
                    manager.disconnect(user_id, ws)
                except Exception:
                    pass
        except asyncio.CancelledError:
            logger.info(f'WS cleaner stopped')
            raise
        except Exception as e:
            logger.error(f'WS cleaner error: {e}')
