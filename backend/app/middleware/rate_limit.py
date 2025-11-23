"""Rate limiting middleware."""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from time import time
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory storage."""

    def __init__(self, app):
        """Initialize rate limiter.

        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.requests = defaultdict(list)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.limit = settings.RATE_LIMIT_PER_MINUTE

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            HTTP response

        Raises:
            HTTPException: If rate limit exceeded
        """
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host
        current_time = time()

        # Clean old requests (older than 60 seconds)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.requests[client_ip]) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        return await call_next(request)
