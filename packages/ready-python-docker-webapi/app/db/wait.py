"""等待 PostgreSQL 可用（容器 entrypoint 用；不經 ORM）。

用法：``python -m app.db.wait``，成功 exit 0，超時 exit 1。
"""

import asyncio
import os
import sys

import asyncpg

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

DEFAULT_MAX_ATTEMPTS = 30
DEFAULT_DELAY_SECONDS = 2.0
CONNECT_TIMEOUT_SECONDS = 5


async def wait_for_database(max_attempts: int, delay_seconds: float) -> bool:
    """以指數式不變的重試間隔等待 DB；成功回傳 True。"""
    settings = get_settings()
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await asyncpg.connect(
                dsn=settings.asyncpg_dsn,
                timeout=CONNECT_TIMEOUT_SECONDS,
            )
        except Exception as exc:  # 任何連線失敗都當作「未就緒」重試
            logger.warning("PostgreSQL 尚未就緒（%d/%d）：%s", attempt, max_attempts, exc)
            if attempt < max_attempts:
                await asyncio.sleep(delay_seconds)
            continue
        await connection.close()
        logger.info("PostgreSQL 已就緒（第 %d 次嘗試）", attempt)
        return True
    return False


def _read_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning("環境變數 %s=%r 不是整數，使用預設值 %d", name, raw, default)
        return default


def _read_float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        logger.warning("環境變數 %s=%r 不是數字，使用預設值 %s", name, raw, default)
        return default


def main() -> int:
    """CLI 入口：等待 DB，回傳 process exit code。"""
    configure_logging(os.environ.get("LOG_LEVEL", "INFO"))
    max_attempts = _read_int_env("DB_WAIT_MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS)
    delay_seconds = _read_float_env("DB_WAIT_DELAY_SECONDS", DEFAULT_DELAY_SECONDS)
    if asyncio.run(wait_for_database(max_attempts, delay_seconds)):
        return 0
    logger.error("等待 PostgreSQL 超時（%d 次嘗試）", max_attempts)
    return 1


if __name__ == "__main__":
    sys.exit(main())
