"""pytest fixtures：用 SQLite + aiosqlite 取代真實 PostgreSQL。

測試不得依賴網絡或 Docker；每個 test 用獨立嘅暫存 DB file，覆蓋 FastAPI 的
`get_session` 依賴，令 app 完全唔會嘗試連 PostgreSQL。
"""

from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


@pytest.fixture
async def engine(tmp_path: Path) -> AsyncGenerator[AsyncEngine, None]:
    """每個 test 一個獨立 SQLite 檔案 DB，並建立所有表。"""
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(
    engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """綁定測試 engine 的 session factory。"""
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
async def app(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[FastAPI, None]:
    """建立 app 並以 SQLite session 覆蓋 `get_session`。"""
    application = create_app()

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_session] = override_get_session
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """直接的 in-process HTTP client（不開 socket）。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client
