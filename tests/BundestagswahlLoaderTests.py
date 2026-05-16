"""Integration tests for bundestagswahl_loader.py.

Uses the real btw2021_wahlkreise.csv data file that ships with the repo.
Most mutants set variables to None or corrupt column names; calling the
loader and verifying basic structural properties kills them.
"""
import pytest
from pathlib import Path
from ipres.bundestagswahl_loader import load_bundestagswahl_data, filter_major_parties


# ---- load_bundestagswahl_data ----

def test_load_2021_returns_correct_types():
    """Mutants #260, #302: vote_matrix or party_names set to None — unpacking fails."""
    constituencies, vote_matrix, party_names = load_bundestagswahl_data(2021)
    assert constituencies is not None
    assert vote_matrix is not None
    assert party_names is not None


def test_load_2021_returns_299_constituencies():
    """Mutants #256-265, #270-277: wrong filter or column names → wrong count or crash."""
    constituencies, _, _ = load_bundestagswahl_data(2021)
    assert len(constituencies) == 299


def test_load_2021_constituencies_has_required_columns():
    """Mutants #271, #273: output column named 'XXconstituency_nameXX' etc."""
    constituencies, _, _ = load_bundestagswahl_data(2021)
    assert "constituency_name" in constituencies.columns
    assert "constituency_size" in constituencies.columns


def test_load_2021_vote_matrix_has_party_columns():
    """Mutants #281-295: wrong filter or column names → SPD absent or empty."""
    _, vote_matrix, party_names = load_bundestagswahl_data(2021)
    assert "SPD" in party_names
    assert "CDU" in party_names
    assert "SPD" in vote_matrix.columns


def test_load_2021_vote_matrix_shape():
    """Mutants #280-301: wrong Stimme filter or pivot corrupted — wrong shape."""
    _, vote_matrix, party_names = load_bundestagswahl_data(2021)
    assert vote_matrix.shape[0] == 299
    assert vote_matrix.shape[1] == len(party_names)


def test_load_2021_vote_matrix_no_negative_values():
    """Mutant #300: fillna(1) instead of fillna(0) — no zeros, minimum is 1."""
    _, vote_matrix, _ = load_bundestagswahl_data(2021)
    assert (vote_matrix >= 0).all().all()


def test_load_2021_spd_votes_positive():
    """Mutant #284: Stimme != 2 filter — Zweitstimmen absent, SPD has 0 votes."""
    _, vote_matrix, _ = load_bundestagswahl_data(2021)
    assert vote_matrix["SPD"].sum() > 0


def test_load_nonexistent_year_raises():
    """Mutant #248: inverted exists() check — raises on real file, silent on missing."""
    with pytest.raises(FileNotFoundError, match=r"Data file not found"):
        load_bundestagswahl_data(1800)


def test_load_with_explicit_data_dir():
    """Mutant #234: inverted data_dir is None check — explicit dir is overridden."""
    from ipres.utils.paths import find_project_root
    data_dir = find_project_root() / "data" / "bundestagswahl"
    constituencies, vote_matrix, party_names = load_bundestagswahl_data(2021, data_dir=data_dir)
    assert len(constituencies) == 299


# ---- filter_major_parties ----

def test_filter_major_parties_reduces_count():
    """Mutant #306/#307: * instead of / or / 100 — percentages wrong → wrong filter."""
    _, vote_matrix, party_names = load_bundestagswahl_data(2021)
    filtered_vm, filtered_names = filter_major_parties(vote_matrix, party_names, min_percent=5.0)
    # 2021: SPD, CDU, Grüne, FDP, AfD, Linke all above 5% nationally
    assert len(filtered_names) < len(party_names)
    assert "SPD" in filtered_names


def test_filter_major_parties_threshold_at_1_percent():
    """Mutant #310: >= becomes > — party with exactly 1% excluded when it shouldn't be."""
    _, vote_matrix, party_names = load_bundestagswahl_data(2021)
    # With 1.0%, more parties survive than with 5.0%
    at_1, names_1 = filter_major_parties(vote_matrix, party_names, min_percent=1.0)
    at_5, names_5 = filter_major_parties(vote_matrix, party_names, min_percent=5.0)
    assert len(names_1) >= len(names_5)


def test_filter_major_parties_returns_correct_types():
    """Mutant #304/#305: total_votes or total_all_votes set to None — crash."""
    _, vote_matrix, party_names = load_bundestagswahl_data(2021)
    filtered_vm, filtered_names = filter_major_parties(vote_matrix, party_names, min_percent=1.0)
    assert filtered_vm is not None
    assert filtered_names is not None
    assert len(filtered_names) > 0
