"""FastAPI application factory 與 lifespan。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import health, items
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """啟動／關閉時的生命週期（migration 由容器 entrypoint 執行）。"""
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("啟動 %s v%s（environment=%s）", app.title, __version__, settings.environment)
    try:
        yield
    finally:
        logger.info("關閉中：dispose 資料庫 engine")
        await dispose_engine()


def create_app(settings: Settings | None = None) -> FastAPI:
    """建立 FastAPI 實例（方便測試注入設定）。"""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="ready-python-docker-webapi",
        summary="FastAPI + async SQLAlchemy + PostgreSQL 示範服務",
        description=(
            "ready-stack 的實戰服務範本：items CRUD、/healthz、/readyz、"
            "Alembic migration、async SQLAlchemy 2 + asyncpg。"
        ),
        version=__version__,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(items.router, prefix="/api/v1")
    return application


app = create_app()
