import pytest
from ipres.utils.paths import find_project_root


def test_find_project_root_default_finds_pyproject():
    """Default marker 'pyproject.toml' is found by traversing up from the working directory.

    Mutant #1821: default marker → 'XXpyproject.tomlXX' — file not found → FileNotFoundError.
    Mutant #1822: *Path().resolve().parents → /Path().resolve().parents — SyntaxError on import.
    Mutant #1823: path / marker → path * marker — TypeError at runtime.
    """
    root = find_project_root()
    assert (root / "pyproject.toml").exists()


def test_find_project_root_not_found_error_message():
    """FileNotFoundError message starts with 'Project root not found'.

    Mutant #1824: XX-prefix on error message — anchored '^Project root' match fails.
    """
    with pytest.raises(FileNotFoundError, match=r"^Project root not found"):
        find_project_root(marker="this_marker_does_not_exist_xyzzy.txt")
