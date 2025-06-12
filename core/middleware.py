import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Simple middleware that logs request and response information."""

    async def dispatch(self, request: Request, call_next):
        logger.info("Request: %s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info(
            "Response: %s %s -> %s", request.method, request.url.path, response.status_code
        )
        return response
