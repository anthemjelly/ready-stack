"""Items CRUD 測試（對應 e2e 合約：201 / list shape / 404 / 204 / PATCH price）。"""

import pytest
from httpx import AsyncClient

ITEMS_PATH = "/api/v1/items"


async def _create_item(
    client: AsyncClient,
    name: str = "widget",
    description: str | None = "a widget",
    price: float = 9.99,
) -> dict[str, object]:
    response = await client.post(
        ITEMS_PATH,
        json={"name": name, "description": description, "price": price},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_item_returns_201_and_item(client: AsyncClient) -> None:
    response = await client.post(
        ITEMS_PATH,
        json={"name": "widget", "description": "a widget", "price": 9.99},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "widget"
    assert body["description"] == "a widget"
    assert body["price"] == pytest.approx(9.99)
    assert not isinstance(body["price"], str), "price 必須是 JSON number，不是字串"
    assert body["created_at"]
    assert body["updated_at"]


async def test_create_item_without_description(client: AsyncClient) -> None:
    response = await client.post(ITEMS_PATH, json={"name": "minimal", "price": "1.50"})

    assert response.status_code == 201
    body = response.json()
    assert body["description"] is None
    assert body["price"] == pytest.approx(1.5)
    assert not isinstance(body["price"], str)


@pytest.mark.parametrize(
    "payload",
    [
        {"price": 1.0},
        {"name": "", "price": 1.0},
        {"name": "x" * 101, "price": 1.0},
        {"name": "ok", "price": -1},
        {"name": "ok", "price": 1.999},
        {"name": "ok"},
    ],
)
async def test_create_item_validation_errors(
    client: AsyncClient, payload: dict[str, object]
) -> None:
    response = await client.post(ITEMS_PATH, json=payload)

    assert response.status_code == 422


async def test_list_items_returns_pagination_shape(client: AsyncClient) -> None:
    await _create_item(client, name="one", price=1.0)
    await _create_item(client, name="two", price=2.0)
    await _create_item(client, name="three", price=3.0)

    response = await client.get(ITEMS_PATH)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert body["total"] == 3
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert [item["id"] for item in body["items"]] == [1, 2, 3]


async def test_list_items_honours_limit_and_offset(client: AsyncClient) -> None:
    for index in range(3):
        await _create_item(client, name=f"item-{index}", price=float(index))

    response = await client.get(ITEMS_PATH, params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert [item["id"] for item in body["items"]] == [2, 3]


async def test_list_items_is_empty_on_empty_database(client: AsyncClient) -> None:
    response = await client.get(ITEMS_PATH)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"limit": "abc"}],
)
async def test_list_items_rejects_invalid_pagination(
    client: AsyncClient, params: dict[str, str | int]
) -> None:
    response = await client.get(ITEMS_PATH, params=params)

    assert response.status_code == 422


async def test_get_item_returns_item(client: AsyncClient) -> None:
    created = await _create_item(client, name="detail")

    response = await client.get(f"{ITEMS_PATH}/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["name"] == "detail"


async def test_get_missing_item_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"{ITEMS_PATH}/999")

    assert response.status_code == 404


async def test_patch_item_updates_price(client: AsyncClient) -> None:
    created = await _create_item(client, name="patch-me", price=9.99)

    response = await client.patch(f"{ITEMS_PATH}/{created['id']}", json={"price": 12.5})

    assert response.status_code == 200
    body = response.json()
    assert body["price"] == pytest.approx(12.5)
    assert not isinstance(body["price"], str)
    assert body["name"] == "patch-me"


async def test_patch_item_can_clear_description(client: AsyncClient) -> None:
    created = await _create_item(client, description="will be removed")

    response = await client.patch(f"{ITEMS_PATH}/{created['id']}", json={"description": None})

    assert response.status_code == 200
    assert response.json()["description"] is None


@pytest.mark.parametrize("payload", [{"name": None}, {"price": None}, {"price": -5}])
async def test_patch_item_validation_errors(
    client: AsyncClient, payload: dict[str, object]
) -> None:
    created = await _create_item(client)

    response = await client.patch(f"{ITEMS_PATH}/{created['id']}", json=payload)

    assert response.status_code == 422


async def test_patch_missing_item_returns_404(client: AsyncClient) -> None:
    response = await client.patch(f"{ITEMS_PATH}/999", json={"name": "nope"})

    assert response.status_code == 404


async def test_delete_item_returns_204_then_get_returns_404(client: AsyncClient) -> None:
    created = await _create_item(client)

    delete_response = await client.delete(f"{ITEMS_PATH}/{created['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = await client.get(f"{ITEMS_PATH}/{created['id']}")
    assert get_response.status_code == 404

    second_delete = await client.delete(f"{ITEMS_PATH}/{created['id']}")
    assert second_delete.status_code == 404
