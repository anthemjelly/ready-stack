"""核心業務邏輯。

呢個模組故意唔 import argparse、唔 print、唔讀環境變數：純輸入輸出，
所以可以直接被 CLI、測試、或者將來嘅 web handler 重用。
"""

__all__ = ["greet"]


def greet(name: str) -> str:
    """回傳向 *name* 打招呼嘅字串。

    Args:
        name: 要打招呼嘅名字。空字串或者只有空白字元會被視為無效。

    Returns:
        格式為 ``Hello, {name}!`` 嘅字串；*name* 本身唔會被 trim。

    Raises:
        ValueError: 當 *name* 係空字串或者只有空白字元時。
    """
    if not name.strip():
        raise ValueError("name 不可以是空字串")
    return f"Hello, {name}!"
