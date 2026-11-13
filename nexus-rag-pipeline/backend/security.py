"""Security middleware for production FastAPI applications."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses.
    
    Implements OWASP recommendations for HTTP security headers.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy - don't leak referrer to external sites
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Feature policy - restrict browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Strict Transport Security - require HTTPS (only in production)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        return response
