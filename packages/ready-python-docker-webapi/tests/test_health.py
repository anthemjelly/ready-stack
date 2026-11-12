"""健康檢查測試。"""

from collections.abc import AsyncGenerator

import pytest
from app.db.session import get_session
from fastapi import FastAPI
from httpx import AsyncClient


class _BrokenSession:
    """假 session：任何 query 都失敗，模擬 DB 斷線。"""

    async def execute(self, *args: object, **kwargs: object) -> object:
        raise RuntimeError("database is down")


async def test_healthz_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readyz_returns_ready_when_database_works(client: AsyncClient) -> None:
    response = await client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


async def test_readyz_returns_503_when_database_fails(app: FastAPI, client: AsyncClient) -> None:
    async def broken_session() -> AsyncGenerator[_BrokenSession, None]:
        yield _BrokenSession()

    app.dependency_overrides[get_session] = broken_session

    response = await client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "error"}


async def test_openapi_schema_is_served(client: AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "ready-python-docker-webapi"
    assert "/api/v1/items" in schema["paths"]


@pytest.mark.parametrize("path", ["/healthz", "/readyz"])
async def test_health_endpoints_are_public(client: AsyncClient, path: str) -> None:
    """健康檢查不應要求認證（現階段整個 API 都無認證）。"""
    response = await client.get(path)

    assert response.status_code in {200, 503}
