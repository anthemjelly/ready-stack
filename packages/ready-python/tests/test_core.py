"""``ready_python.core`` 嘅單元測試（正常路徑 + 錯誤路徑）。"""

import pytest

from ready_python.core import greet


@pytest.mark.parametrize("name", ["World", "Alice", "世界", "Alice Smith", "  Ann  "])
def test_greet_returns_hello_message(name: str) -> None:
    # greet() 只負責驗證同格式化，唔會 trim 名字本身。
    assert greet(name) == f"Hello, {name}!"


@pytest.mark.parametrize("name", ["", " ", "\t", "\n", "   \t  "])
def test_greet_rejects_empty_or_blank_name(name: str) -> None:
    with pytest.raises(ValueError):
        greet(name)


def test_greet_error_message_mentions_name() -> None:
    with pytest.raises(ValueError, match="name"):
        greet("")
