"""Tests for the PyInstaller hook support module."""

from pathlib import Path


def test_get_hook_dirs_returns_list():
    from newspaper._pyinstaller import get_hook_dirs

    hook_dirs = get_hook_dirs()
    assert isinstance(hook_dirs, list)
    assert len(hook_dirs) == 1


def test_get_hook_dirs_directory_exists():
    from newspaper._pyinstaller import get_hook_dirs

    hook_dir = Path(get_hook_dirs()[0])
    assert hook_dir.is_dir()


def test_hook_file_exists():
    from newspaper._pyinstaller import get_hook_dirs

    hook_dir = Path(get_hook_dirs()[0])
    hook_file = hook_dir / "hook-newspaper.py"
    assert hook_file.is_file()
