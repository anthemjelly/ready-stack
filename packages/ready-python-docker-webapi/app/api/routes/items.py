"""`/api/v1/items` CRUD 路由。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemList, ItemRead, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LimitQuery = Annotated[int, Query(ge=1, le=100, description="每頁筆數（1-100）")]
OffsetQuery = Annotated[int, Query(ge=0, description="跳過筆數")]

DEFAULT_LIMIT = 20


async def _get_item_or_404(session: AsyncSession, item_id: int) -> Item:
    item = await session.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )
    return item


@router.post(
    "",
    response_model=ItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="新增 item",
)
async def create_item(payload: ItemCreate, session: SessionDep) -> Item:
    item = Item(name=payload.name, description=payload.description, price=payload.price)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.get("", response_model=ItemList, summary="列出 items（分頁）")
async def list_items(
    session: SessionDep,
    limit: LimitQuery = DEFAULT_LIMIT,
    offset: OffsetQuery = 0,
) -> ItemList:
    total = await session.scalar(select(func.count()).select_from(Item)) or 0
    result = await session.execute(select(Item).order_by(Item.id).limit(limit).offset(offset))
    items = [ItemRead.model_validate(row) for row in result.scalars().all()]
    return ItemList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{item_id}", response_model=ItemRead, summary="取得單一 item")
async def get_item(item_id: int, session: SessionDep) -> Item:
    return await _get_item_or_404(session, item_id)


@router.patch("/{item_id}", response_model=ItemRead, summary="局部更新 item")
async def update_item(item_id: int, payload: ItemUpdate, session: SessionDep) -> Item:
    item = await _get_item_or_404(session, item_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        for field, value in updates.items():
            setattr(item, field, value)
        await session.commit()
        await session.refresh(item)
    return item


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="刪除 item",
)
async def delete_item(item_id: int, session: SessionDep) -> Response:
    item = await _get_item_or_404(session, item_id)
    await session.delete(item)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
