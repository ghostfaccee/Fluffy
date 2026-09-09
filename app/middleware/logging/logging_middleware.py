import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.requests import Request

from app.core import logger, yaml_settings

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Optional[Response]:
        start_time = time.time()
        logger.info(f'-> {request.url.path}, {request.method}')
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            if process_time > yaml_settings.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f'Slow request: {request.url.path}, {request.method}'
                    f'Took: {process_time:.2f}s (threshold: {yaml_settings.SLOW_REQUEST_THRESHOLD}s)'
                )
            else:
                logger.info(
                    f'<- {request.url.path}, {request.method}'
                    f'Status: {response.status_code}'
                    f'Process time: {process_time:.2f}s'
                )
            return response
        except Exception as e:
            logger.error(
                f'<- {request.url.path}, {request.method}'
                f'Error: {e}'
            )
            raise