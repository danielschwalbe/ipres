import io
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from ipres.constituencies_config import ConstituenciesConfig


def _make_df(names, sizes, **extra):
    d = {"constituency_name": list(names), "constituency_size": list(sizes)}
    d.update(extra)
    return pd.DataFrame(d)


# ---- fill_random (mutant #1040) ----

def test_fill_random_sets_constituencies():
    """Mutant #1040: self.constituencies = None — constituencies is None after fill_random."""
    cc = ConstituenciesConfig()
    cc.fill_random(3, 100_000, 200_000)
    assert cc.constituencies is not None
    assert len(cc.constituencies) == 3


# ---- set_dataframe (mutant #1042) ----

def test_set_dataframe_updates_constituencies():
    """Mutant #1042: self.constituencies = None — constituencies is None after set_dataframe."""
    cc = ConstituenciesConfig()
    df = _make_df(["C1"], [100_000])
    cc.set_dataframe(df)
    assert cc.constituencies is not None
    assert len(cc.constituencies) == 1


# ---- from_csv classmethod (mutant #1045) ----

def test_from_csv_is_classmethod():
    """Mutant #1045: @classmethod removed — cls bound as path argument, call fails."""
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as f:
        f.write("constituency_name,constituency_size\nC1,100000\n")
        path = f.name
    try:
        cc = ConstituenciesConfig.from_csv(path)
        assert cc.constituencies is not None
        assert len(cc.constituencies) == 1
    finally:
        os.unlink(path)


# ---- _from_random size generation (mutant #1052) ----

def test_from_random_size_bounded_by_smax():
    """Mutant #1052: high=Smax+2 — sizes can exceed Smax."""
    cc = ConstituenciesConfig.from_random(20, 100_000, 100_000)
    sizes = cc.constituencies["constituency_size"].tolist()
    assert all(s == 100_000 for s in sizes)


# ---- _from_random error message (mutant #1056) ----

def test_from_random_nonfinite_turnout_raises():
    """Mutant #1056: XX-prefix on error — anchored match fails on mutant."""
    with pytest.raises(ValueError, match=r"^average_turnout_percent must be a finite number"):
        ConstituenciesConfig.from_random(3, 100_000, 200_000, average_turnout_percent=float("inf"))


# ---- _from_random turnout clamp (mutant #1060) ----

def test_from_random_zero_average_turnout():
    """Mutant #1060: max(1.0, ...) — 0% average is clamped to 1%, votes_cast > 0."""
    cc = ConstituenciesConfig.from_random(5, 100_000, 100_000, average_turnout_percent=0.0)
    votes = cc.constituencies["votes_cast"].tolist()
    assert all(v == 0 for v in votes)


# ---- _from_random votes_cast column name (mutant #1091) ----

def test_from_random_has_votes_cast_column():
    """Mutant #1091: column named 'XXvotes_castXX' — votes_cast absent in result."""
    cc = ConstituenciesConfig.from_random(3, 100_000, 200_000)
    assert "votes_cast" in cc.constituencies.columns


# ---- _from_random votes_cast formula (mutants #1093, #1095) ----

def test_from_random_votes_cast_formula():
    """Mutants #1093 (/ instead of *), #1095 (* 100 instead of / 100) — wrong value."""
    cc = ConstituenciesConfig.from_random(1, 100_000, 100_000, average_turnout_percent=50.0)
    row = cc.constituencies.iloc[0]
    # With M=1 and seed 0, z = rng.standard_normal(1); z - z.mean() = 0; amplitude = 0.
    # turnout = 50.0 exactly. votes_cast = 100_000 * 50.0 / 100 = 50_000.
    assert row["votes_cast"] == 50_000


# ---- _validate_df error message (mutant #1103) ----

def test_validate_df_missing_column_error_message():
    """Mutant #1103: XX-prefix on error — anchored match fails on mutant."""
    df = pd.DataFrame({"wrong_col": [1]})
    with pytest.raises(ValueError, match=r"^Missing required column"):
        ConstituenciesConfig.from_dataframe(df)


# ---- _validate_df column type coercions (mutants #1105, #1108) ----

def test_validate_df_constituency_name_coerced_to_str():
    """Mutant #1105: new column 'XXconstituency_nameXX' created — original stays uncoerced."""
    df = pd.DataFrame({"constituency_name": [1, 2], "constituency_size": [100_000, 200_000]})
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["constituency_name"].iloc[0] == "1"


def test_validate_df_constituency_size_coerced_to_int():
    """Mutant #1108: new column 'XXconstituency_sizeXX' created — original stays as string."""
    df = pd.DataFrame({"constituency_name": ["C1"], "constituency_size": ["100000"]})
    cc = ConstituenciesConfig.from_dataframe(df)
    assert isinstance(cc.constituencies["constituency_size"].iloc[0], (int, np.integer))


# ---- _validate_df optional column detection (mutants #1111, #1113, #1116) ----

def test_validate_df_turnout_present_is_clipped():
    """Mutants #1111/#1113: turnout not detected — clip never runs, value stays >100."""
    df = _make_df(["C1"], [100_000], turnout_percent=[150.0])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["turnout_percent"].iloc[0] == 100.0


def test_validate_df_votes_cast_present_is_coerced():
    """Mutant #1116: has_votes_cast=None — coercion never runs, negative value stays."""
    df = _make_df(["C1"], [100_000], votes_cast=[-500])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["votes_cast"].iloc[0] == 0


# ---- _validate_df turnout NaN fill (mutant #1120) ----

def test_validate_df_turnout_nan_filled_with_zero():
    """Mutant #1120: fillna(1.0) — NaN turnout becomes 1.0 instead of 0.0."""
    df = _make_df(["C1", "C2"], [100_000, 100_000], turnout_percent=[50.0, float("nan")])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["turnout_percent"].iloc[1] == 0.0


# ---- _validate_df turnout clip (mutant #1125) ----

def test_validate_df_turnout_clipped_at_100():
    """Mutant #1125: clip upper=101.0 — value of 100.5 passes through unclipped."""
    df = _make_df(["C1"], [100_000], turnout_percent=[100.5])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["turnout_percent"].iloc[0] == 100.0


# ---- _validate_df turnout round (mutant #1130) ----

def test_validate_df_turnout_rounded_not_none():
    """Mutant #1130: df['turnout_percent'] = None — entire column replaced with None."""
    df = _make_df(["C1"], [100_000], turnout_percent=[75.555])
    cc = ConstituenciesConfig.from_dataframe(df)
    val = cc.constituencies["turnout_percent"].iloc[0]
    assert val is not None
    assert abs(val - 75.56) < 0.01


# ---- _validate_df votes_cast coercion (mutant #1135) ----

def test_validate_df_votes_cast_coerced_not_none():
    """Mutant #1135: df['votes_cast'] = None — entire column replaced with None."""
    df = _make_df(["C1"], [100_000], votes_cast=[75_000])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["votes_cast"].iloc[0] == 75_000


# ---- _validate_df negative votes_cast zeroed (mutant #1140) ----

def test_validate_df_negative_votes_cast_zeroed():
    """Mutant #1140: negative votes set to 1 instead of 0."""
    df = _make_df(["C1"], [100_000], votes_cast=[-999])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["votes_cast"].iloc[0] == 0


# ---- _validate_df derivation: votes_cast from turnout (mutants #1144, #1149) ----

def test_validate_df_derive_votes_cast_column_name():
    """Mutant #1144: column 'XXvotes_castXX' created — 'votes_cast' absent."""
    df = _make_df(["C1"], [100_000], turnout_percent=[50.0])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert "votes_cast" in cc.constituencies.columns


def test_validate_df_derive_votes_cast_value():
    """Mutant #1149: /101.0 instead of /100.0 — derived value ~1% too small."""
    df = _make_df(["C1"], [100_000], turnout_percent=[50.0])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["votes_cast"].iloc[0] == 50_000


# ---- _validate_df derivation: turnout from votes_cast (mutants #1155, #1160, #1165, #1170) ----

def test_validate_df_derive_turnout_no_error():
    """Mutant #1155: invalid np.errstate key raises ValueError."""
    df = _make_df(["C1"], [200_000], votes_cast=[100_000])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies is not None


def test_validate_df_derive_turnout_correct_value():
    """Mutants #1160/#1165: wrong np.where condition or *101 — wrong turnout computed."""
    df = _make_df(["C1"], [200], votes_cast=[100])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["turnout_percent"].iloc[0] == 50.0


def test_validate_df_derive_turnout_zero_size_constituency():
    """Mutant #1170: 0.0 → 1.0 — zero-size constituency gets turnout 1.0 instead of 0.0."""
    df = _make_df(["C1"], [0], votes_cast=[0])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["turnout_percent"].iloc[0] == 0.0


# ---- _validate_df final votes_cast dtype enforcement (mutant #1180) ----

def test_validate_df_votes_cast_int_dtype():
    """Mutant #1180: accesses 'XXvotes_castXX' column — raises KeyError."""
    df = _make_df(["C1"], [100_000], votes_cast=[75_000])
    cc = ConstituenciesConfig.from_dataframe(df)
    assert cc.constituencies["votes_cast"].iloc[0] == 75_000


# ---- save: GUI check (mutant #1280) ----

def test_save_raises_when_filedialog_none():
    """Mutant #1280: inverted _filedialog is not None check — no RuntimeError when _filedialog=None."""
    cc = ConstituenciesConfig.from_random(2, 100_000, 200_000)
    import ipres.constituencies_config as cc_module

    orig_tk, orig_fd = cc_module._tk, cc_module._filedialog
    cc_module._filedialog = None
    cc_module._tk = object()  # not None, but has no Tk() method
    try:
        with pytest.raises(RuntimeError, match=r"No GUI available"):
            cc.save(path=None)
    finally:
        cc_module._tk = orig_tk
        cc_module._filedialog = orig_fd


# ---- save: success message (mutant #1312) ----

def test_save_prints_success_message(capsys):
    """Mutant #1312: XX-prefix on success message — anchored match fails on mutant."""
    cc = ConstituenciesConfig.from_random(2, 100_000, 200_000)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "constituencies.csv")
        cc.save(path=path)
    captured = capsys.readouterr()
    assert captured.out.startswith("Successfully saved constituencies to:")
