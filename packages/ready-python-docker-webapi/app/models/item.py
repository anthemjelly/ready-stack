"""ORM model：`items` 表。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Identity, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Item(Base):
    """一筆示範資料（名稱、描述、價格、時間戳）。"""

    __tablename__ = "items"

    # PostgreSQL 用 IDENTITY 自增；SQLite（單元測試）用 INTEGER PRIMARY KEY 自增。
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        Identity(always=False),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - 只為 debug 輸出
        return f"Item(id={self.id!r}, name={self.name!r}, price={self.price!r})"
