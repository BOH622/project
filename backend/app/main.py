"""FastAPI app factory."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.events.bus import bus
from app.middleware.readonly_impersonation import ReadOnlyImpersonationMiddleware
from app.routes import admin, auth, health, webhooks_inbound
from app.webhooks.dispatcher import dispatch


def create_app() -> FastAPI:
    app = FastAPI(
        title="UserCue Projects Portal",
        description="Provider-facing portal API",
        version="0.1.0",
    )

    app.add_middleware(ReadOnlyImpersonationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(webhooks_inbound.router)

    # Wire the outbound webhook dispatcher as a global subscriber.
    # Any bus.publish(event) automatically fans out to registered OutboundWebhooks.
    bus.subscribe(None, dispatch)

    return app


app = create_app()
