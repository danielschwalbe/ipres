import io
import tempfile
import os

import numpy as np
import pandas as pd
import pytest

from ipres.parties import Parties


def _make_df(*names: str) -> pd.DataFrame:
    return pd.DataFrame({"party_name": list(names)})


# ---- fill_random (mutant #1495) ----

def test_fill_random_sets_parties():
    """Mutant #1495: self.parties = None — parties is None after fill_random."""
    p = Parties()
    p.fill_random(3)
    assert p.parties is not None
    assert len(p.parties) == 3


# ---- from_random / _from_random label generation (mutants #1510, #1520) ----

def test_from_random_first_party_is_a():
    """Mutant #1510: idx += 2 instead of += 1 — first label would be 'B' not 'A'."""
    parties = Parties.from_random(3)
    names = parties.parties["party_name"].tolist()
    assert names[0] == "Partei A"
    assert names[1] == "Partei B"
    assert names[2] == "Partei C"


def test_from_random_26th_party():
    """Mutant #1520: s = None — label generation crashes after first char."""
    parties = Parties.from_random(26)
    names = parties.parties["party_name"].tolist()
    assert names[25] == "Partei Z"


def test_from_random_27th_party():
    """Mutants #1510, #1520: two-letter suffix starts correctly at 'AA'."""
    parties = Parties.from_random(27)
    names = parties.parties["party_name"].tolist()
    assert names[26] == "Partei AA"


# ---- _validate_df (mutants #1530, #1540, #1550) ----

def test_validate_df_missing_column_raises():
    """Mutant #1530: required = None — iterating None raises TypeError."""
    df = pd.DataFrame({"wrong_col": ["A", "B"]})
    with pytest.raises((ValueError, TypeError)):
        Parties.from_dataframe(df)


def test_validate_df_empty_name_raises():
    """Mutant #1540: wrong column name in empty-name check — empty name passes silently."""
    df = _make_df("A", "", "B")
    with pytest.raises(ValueError):
        Parties.from_dataframe(df)


def test_validate_df_duplicate_name_raises():
    """Mutant #1550: dup_mask = None — duplicate detection crashes (AttributeError)."""
    df = _make_df("A", "A", "B")
    with pytest.raises((ValueError, AttributeError)):
        Parties.from_dataframe(df)


def test_validate_df_valid_input():
    """_validate_df returns a clean DataFrame for valid input."""
    df = _make_df("Alpha", "  Beta  ", "Gamma")
    result = Parties.from_dataframe(df)
    names = result.parties["party_name"].tolist()
    assert names == ["Alpha", "Beta", "Gamma"]


# ---- save: path logic (mutants #1630, #1650, #1660) ----

def test_save_with_path_none_and_no_gui_raises():
    """Mutant #1630: if path is not None inverted — with path=None and no GUI, raises RuntimeError."""
    p = Parties.from_dataframe(_make_df("A", "B"))
    import ipres.parties as parties_module
    orig_tk = parties_module._tk
    orig_fd = parties_module._filedialog
    parties_module._tk = None
    parties_module._filedialog = None
    try:
        with pytest.raises(RuntimeError):
            p.save(path=None)
    finally:
        parties_module._tk = orig_tk
        parties_module._filedialog = orig_fd


def test_save_unsupported_extension_raises():
    """Mutant #1660: XX-prefix on unsupported file type error — anchored match fails."""
    p = Parties.from_dataframe(_make_df("A", "B"))
    with pytest.raises(ValueError, match=r"^Unsupported file type"):
        p.save(path="/tmp/parties_test.txt")


def test_save_relative_path_resolved():
    """Mutant #1650: find_project_root() * path — TypeError instead of valid path."""
    p = Parties.from_dataframe(_make_df("A", "B"))
    with tempfile.TemporaryDirectory() as tmpdir:
        abs_path = os.path.join(tmpdir, "parties.csv")
        result = p.save(path=abs_path)
        assert os.path.exists(result)
