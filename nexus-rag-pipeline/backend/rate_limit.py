"""Rate limiting middleware for production FastAPI applications."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting by IP address with sliding window counters.
    
    Tracks requests per minute and per hour using in-memory storage.
    For distributed systems, consider Redis-based rate limiting.
    """

    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        # Structure: {ip: [(timestamp, endpoint), ...]}
        self.request_history: defaultdict[str, list[tuple[float, str]]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Any:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        current_time = time.time()

        # Cleanup old entries
        minute_ago = current_time - 60
        hour_ago = current_time - 3600

        if client_ip in self.request_history:
            self.request_history[client_ip] = [
                (ts, ep) for ts, ep in self.request_history[client_ip] if ts > hour_ago
            ]

        # Count requests in different time windows
        requests_minute = sum(1 for ts, _ in self.request_history[client_ip] if ts > minute_ago)
        requests_hour = len(self.request_history[client_ip])

        # Check rate limits
        if requests_minute >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded: 60 requests per minute",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        if requests_hour >= self.requests_per_hour:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded: 1000 requests per hour",
                    "retry_after": 3600,
                },
                headers={"Retry-After": "3600"},
            )

        # Record this request
        self.request_history[client_ip].append((current_time, endpoint))

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            self.requests_per_minute - requests_minute - 1
        )
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            self.requests_per_hour - requests_hour - 1
        )

        return response
