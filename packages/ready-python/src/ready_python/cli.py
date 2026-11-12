"""``ready-python`` 嘅命令列介面。

只用標準庫 ``argparse``，方便直接複製去新專案；``main()`` 回傳 exit code，
唔會自己叫 ``sys.exit``，所以測試可以純粹呼叫 ``main([...])``。
"""

import argparse
import sys
from collections.abc import Sequence

from ready_python import __version__
from ready_python.core import greet

EXIT_OK = 0
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    """建立 CLI parser（獨立成函數，方便測試同擴充）。"""
    parser = argparse.ArgumentParser(
        prog="ready-python",
        description="ready-stack 起手模板嘅示範 CLI。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="顯示版本並結束",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    greet_parser = subparsers.add_parser(
        "greet",
        help="向指定嘅名字打招呼",
        description="印出 Hello, <name>!；名字唔可以係空白。",
    )
    greet_parser.add_argument(
        "--name",
        required=True,
        metavar="NAME",
        help="要打招呼嘅名字",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI 入口。

    Args:
        argv: 參數列表（唔包程式名）。``None`` 代表用 ``sys.argv[1:]``。

    Returns:
        Process exit code：成功係 ``0``，使用錯誤係 ``2``。
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return EXIT_OK

    if args.command == "greet":
        try:
            print(greet(args.name))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_USAGE
        return EXIT_OK

    parser.error(f"unknown command: {args.command}")
