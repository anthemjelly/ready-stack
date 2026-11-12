"""Pydantic schemas：items API 的請求／回應格式。"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

# DB 是 numeric(10, 2)。輸入用 Decimal 驗證；
# 輸出時強制序列化成 JSON number（Pydantic v2 預設會把 Decimal 變字串，
# 會破壞 `{"price": 9.99}` 這個 API 合約）。
PriceInput = Annotated[
    Decimal,
    Field(ge=Decimal("0"), max_digits=10, decimal_places=2, description="價格（最多 2 位小數）"),
]
PriceOut = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]


class ItemCreate(BaseModel):
    """POST /api/v1/items 的請求 body。"""

    name: Annotated[str, Field(min_length=1, max_length=100, description="名稱")]
    description: Annotated[str | None, Field(default=None, max_length=500, description="描述")] = (
        None
    )
    price: PriceInput


class ItemUpdate(BaseModel):
    """PATCH /api/v1/items/{id} 的請求 body：所有欄位皆為選填。"""

    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None
    description: Annotated[str, Field(max_length=500)] | None = None
    price: Annotated[Decimal, Field(ge=Decimal("0"), max_digits=10, decimal_places=2)] | None = None

    @field_validator("name", "price")
    @classmethod
    def _reject_explicit_null(cls, value: object) -> object:
        """`null` 不能用來清空 not-null 欄位（省略欄位才是「不改」）。"""
        if value is None:
            msg = "欄位不可為 null；如不想修改請省略該欄位"
            raise ValueError(msg)
        return value


class ItemRead(BaseModel):
    """單筆 item 的回應格式。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: PriceOut
    created_at: datetime
    updated_at: datetime


class ItemList(BaseModel):
    """列表回應：items + 分頁資訊。"""

    items: list[ItemRead]
    total: int
    limit: int
    offset: int
