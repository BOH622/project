"""Defense-in-depth: reject write methods while an impersonation cookie is present.

The primary enforcement is `reject_if_impersonating` as a per-route dependency.
This middleware catches any mutation route that forgets to attach the dependency.
"""
from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.auth.session import COOKIE_NAME, InvalidSession, verify

WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Admin impersonate/stop must work even while impersonating.
EXEMPT_PATHS = {"/admin/impersonate/stop", "/auth/logout"}


class ReadOnlyImpersonationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in WRITE_METHODS:
            return await call_next(request)
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        cookie = request.cookies.get(COOKIE_NAME)
        if cookie:
            try:
                _, imp_id = verify(cookie)
            except InvalidSession:
                return await call_next(request)  # let the dependency layer 401 it
            if imp_id is not None:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "read-only during impersonation"},
                )

        return await call_next(request)
