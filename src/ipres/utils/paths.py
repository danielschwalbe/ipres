"""Utilities for locating the project root directory."""

from pathlib import Path


def find_project_root(marker: str = "pyproject.toml") -> Path:
    """Search upward from the current working directory until a marker file is found.

    Args:
        marker: Filename that identifies the project root. Defaults to "pyproject.toml".

    Returns:
        Path to the project root directory.

    Raises:
        FileNotFoundError: If no directory containing the marker file is found.
    """
    for path in [Path().resolve(), *Path().resolve().parents]:
        if (path / marker).exists():
            return path
    raise FileNotFoundError(f"Project root not found (marker: {marker})")
