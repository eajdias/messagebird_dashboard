"""
Middleware Configuration
"""

import logging
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("m_bird.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status code and duration."""

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:8]
        method = request.method
        path = request.url.path
        start = time.perf_counter()

        # Attach request_id so downstream code can reference it
        request.state.request_id = request_id

        logger.info("[%s] --> %s %s", request_id, method, path)

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception("[%s] <-- %s %s ERROR (%.1fms)", request_id, method, path, duration_ms)
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        status = response.status_code
        level = logging.WARNING if status >= 400 else logging.INFO

        logger.log(
            level,
            "[%s] <-- %s %s %d (%.1fms)",
            request_id,
            method,
            path,
            status,
            duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response


def setup_middleware(app: FastAPI) -> None:
    """Configure CORS, request logging, and other middleware."""
    import os

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
