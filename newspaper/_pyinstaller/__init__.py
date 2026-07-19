"""PyInstaller hooks for newspaper4k.

This module provides the hook directory to PyInstaller via the
``pyinstaller40`` entry point so that all newspaper resource files
(stopwords, user-agents, etc.) are bundled automatically when an
application that uses newspaper4k is frozen with PyInstaller.
"""

from pathlib import Path


def get_hook_dirs() -> list[str]:
    """Return the directory that contains the newspaper PyInstaller hook."""
    return [str(Path(__file__).parent)]
