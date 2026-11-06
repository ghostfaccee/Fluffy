import traceback
import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core import RedisClient, logger
from app.api import router
from app.exceptions import user as user_exc
from app.middleware import LoggingMiddleware
from app.infrastructure import PubSubService
from app.infrastructure.websocket.cleanup import cleanup_stale_connections
from app.infrastructure.websocket.pubsub import listen_ws_channel_with_reconnect

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await (await RedisClient.get_client()).ping()
    logger.info('Fluffy started')

    ws_listener = asyncio.create_task(listen_ws_channel_with_reconnect())
    ws_cleaner = asyncio.create_task(cleanup_stale_connections())

    yield

    ws_listener.cancel()
    ws_cleaner.cancel()

    for task in (ws_listener, ws_cleaner):
        try:
            await task
        except asyncio.CancelledError:
            pass

    await RedisClient.close()
    logger.info('Fluffy stopped')

app = FastAPI(lifespan = lifespan)

# handler for unforeseen errors
@app.exception_handler(Exception)
async def global_exc_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f'Unhandled error on {request.method} {request.url.path}\n'
        f'{traceback.format_exc()}'
    )
    return JSONResponse(
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, 
        content = {'detail': 'Internal Server Error'}
    )

app.add_middleware(LoggingMiddleware)
app.include_router(router)