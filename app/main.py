import traceback
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core import RedisClient, logger
from app.api import router # !!!!
from app.middleware import LoggingMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await (await RedisClient.get_client()).ping()
    logger.info('Fluffy started')
    yield
    await (await RedisClient.get_client()).close()
    logger.info('Fluffy stopped')

app = FastAPI(lifespan = lifespan)

@app.exception_handler(Exception)
async def global_exc_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f'Unhandled error on {request.method} {request.url.path}\n',
    f'{traceback.format_exc()}')
    return JSONResponse(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, content = {'detatil': 'Internal Server Error'})

app.add_middleware(LoggingMiddleware)
app.include_router(router)