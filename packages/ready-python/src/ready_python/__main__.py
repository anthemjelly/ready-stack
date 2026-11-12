"""``python -m ready_python`` 嘅入口，對應 ``pyproject.toml`` 入面嘅 console script。"""

from ready_python.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
