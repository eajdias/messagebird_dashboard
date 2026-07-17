from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.dependencies import stop_pool
from api.middleware import setup_middleware
from api.routes import admin, auth, conversations, dashboard, reports
from infrastructure.config.config_loader import load_and_configure_business, load_bsc_config


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    import os

    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    config_path = os.path.join(os.path.dirname(__file__), "..", "business_config.yaml")
    bsc_path = os.path.join(os.path.dirname(__file__), "..", "business_bsc.yaml")
    load_and_configure_business(config_path)
    load_bsc_config(bsc_path)

    yield

    await stop_pool()


def create_app() -> FastAPI:
    app = FastAPI(
        title="MBird Reporting API",
        description="Omnichannel Reporting Tool - API REST",
        version="2.0.0",
        lifespan=lifespan,
    )

    setup_middleware(app)

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    return app


app = create_app()
