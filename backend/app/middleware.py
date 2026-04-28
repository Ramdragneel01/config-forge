from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class HostAllowlistMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_hosts: list[str]):
        super().__init__(app)
        self.allowed_hosts = {host.lower() for host in allowed_hosts}

    async def dispatch(self, request: Request, call_next):
        host_header = request.headers.get("host", "").split(":", 1)[0].lower()
        if host_header and host_header not in self.allowed_hosts:
            return JSONResponse(status_code=400, content={"detail": "Host is not allowed"})
        return await call_next(request)


class PayloadSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_payload_bytes: int):
        super().__init__(app)
        self.max_payload_bytes = max_payload_bytes

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_payload_bytes:
                return JSONResponse(status_code=413, content={"detail": "Payload too large"})
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enable_hsts: bool):
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'"
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response
