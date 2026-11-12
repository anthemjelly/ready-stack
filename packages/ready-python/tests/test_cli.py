"""``ready_python.cli`` 嘅行為測試：參數、stdout/stderr、exit code 同 ``python -m``。"""

import subprocess
import sys

import pytest

from ready_python import __version__
from ready_python.cli import main


def test_greet_command_prints_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["greet", "--name", "World"]) == 0

    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"
    assert captured.err == ""


def test_greet_command_with_empty_name_returns_usage_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["greet", "--name", ""]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error:")


def test_greet_requires_name_argument(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["greet"])

    assert excinfo.value.code == 2
    assert "--name" in capsys.readouterr().err


def test_version_flag_prints_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])

    assert excinfo.value.code == 0
    assert capsys.readouterr().out.strip() == f"ready-python {__version__}"


def test_no_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0

    assert "usage: ready-python" in capsys.readouterr().out


def test_module_entry_point() -> None:
    """``python -m ready_python`` 要同 console script 行同一個入口。"""
    result = subprocess.run(
        [sys.executable, "-m", "ready_python", "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == f"ready-python {__version__}"
