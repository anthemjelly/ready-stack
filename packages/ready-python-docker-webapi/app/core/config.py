"""應用設定：由環境變數／`.env` 載入（pydantic-settings）。"""

from functools import lru_cache
from urllib.parse import quote

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """所有可調參數的單一來源。

    優先次序：環境變數 > `.env` > 此處的預設值。`DATABASE_URL` 如有設定，
    會完整覆寫由 `POSTGRES_*` 組合出來的 DSN。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- PostgreSQL ---
    postgres_user: str = Field(default="webapi", description="PostgreSQL 使用者")
    postgres_password: str = Field(default="webapi", description="PostgreSQL 密碼")
    postgres_db: str = Field(default="webapi", description="PostgreSQL 資料庫名稱")
    postgres_host: str = Field(default="localhost", description="PostgreSQL 主機")
    postgres_port: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL 端口")
    database_url: str = Field(
        default="",
        description="完整非同步 DSN；有值時覆寫 POSTGRES_* 的組合",
    )

    # --- 應用行為 ---
    environment: str = Field(
        default="development", description="環境名稱（development/staging/production）"
    )
    log_level: str = Field(default="INFO", description="日誌等級")
    run_migrations: bool = Field(default=True, description="容器啟動時是否執行 Alembic migration")
    cors_origins: str = Field(
        default="http://localhost:8000,http://localhost:3000",
        description="允許的 CORS origin，以逗號分隔",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """把逗號分隔的 `CORS_ORIGINS` 轉成 list（空白項目會剔除）。"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        """SQLAlchemy 用的 asyncpg DSN（`postgresql+asyncpg://...`）。"""
        if self.database_url:
            return self._normalize(self.database_url)
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password, safe="")
        database = quote(self.postgres_db, safe="")
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{database}"
        )

    @property
    def asyncpg_dsn(self) -> str:
        """給 `asyncpg.connect()` 直接使用的 DSN（`postgresql://...`）。"""
        return self.async_database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    @staticmethod
    def _normalize(url: str) -> str:
        """接受 `postgresql://`、`postgres://` 或已帶 asyncpg driver 的 DSN。"""
        if url.startswith("postgresql+asyncpg://"):
            return url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """回傳快取後的 Settings 單例（每個 process 只建一次）。"""
    return Settings()
