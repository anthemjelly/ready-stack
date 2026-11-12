"""健康檢查：`/healthz`（liveness）與 `/readyz`（readiness，會查 DB）。"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_session

logger = get_logger(__name__)

router = APIRouter(tags=["health"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class HealthStatus(BaseModel):
    """健康檢查回應。"""

    status: str


class ReadyStatus(BaseModel):
    """Readiness 回應。"""

    status: str
    database: str


@router.get("/healthz", response_model=HealthStatus, summary="Liveness 檢查")
async def healthz() -> HealthStatus:
    """只證明 process 活著，不碰資料庫。"""
    return HealthStatus(status="ok")


@router.get(
    "/readyz",
    response_model=None,
    responses={
        200: {"model": ReadyStatus, "description": "服務與資料庫都就緒"},
        503: {"model": ReadyStatus, "description": "資料庫無法連線"},
    },
    summary="Readiness 檢查（會執行 SELECT 1）",
)
async def readyz(session: SessionDep) -> JSONResponse:
    """執行 `SELECT 1`；DB 不可用時回 503。"""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # 任何 DB 錯誤都應回報 503 而不是 500
        logger.exception("readiness 檢查失敗：資料庫無法連線")
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "database": "error"},
        )
    return JSONResponse(content={"status": "ready", "database": "ok"})
