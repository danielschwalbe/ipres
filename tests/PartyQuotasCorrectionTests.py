import numpy as np
import pytest

from ipres.election_config import QuotaCorrectionStrategy
from ipres.party_quotas_correction import correct_party_quotas


def _seats_to_quotas(seats: dict) -> dict:
    """Compute base quotas as seats // 2 per party."""
    return {p: s // 2 for p, s in seats.items()}


# ---- NEGOTIATED strategy error messages ----

def test_negotiated_strategy_requires_callback():
    """NEGOTIATED without a callback raises ValueError.

    Mutant #1344: XX-prefix on message — anchored match fails.
    """
    seats = {'A': 3, 'B': 3}
    quotas = _seats_to_quotas(seats)
    with pytest.raises(ValueError, match=r"^NEGOTIATED strategy requires"):
        correct_party_quotas(quotas, seats, QuotaCorrectionStrategy.NEGOTIATED)


def test_negotiated_callback_must_return_list_or_set():
    """NEGOTIATED callback returning wrong type raises ValueError.

    Mutant #1347: XX-prefix on message — anchored match fails.
    """
    seats = {'A': 3, 'B': 3}
    quotas = _seats_to_quotas(seats)
    with pytest.raises(ValueError, match=r"^Callback must return a list or set"):
        correct_party_quotas(quotas, seats, QuotaCorrectionStrategy.NEGOTIATED,
                             callback=lambda odd, deficit: "wrong_type")


def test_negotiated_callback_must_return_correct_count():
    """NEGOTIATED callback returning wrong number of parties raises ValueError.

    Mutant #1349: XX-prefix on message — anchored match fails.
    """
    seats = {'A': 3, 'B': 3}
    quotas = _seats_to_quotas(seats)
    with pytest.raises(ValueError, match=r"^Callback must return exactly"):
        correct_party_quotas(quotas, seats, QuotaCorrectionStrategy.NEGOTIATED,
                             callback=lambda odd, deficit: [])


# ---- RANDOM strategy: rng determinism and no duplicate selection ----

def test_random_strategy_is_deterministic_with_rng():
    """Two fresh rngs of the same seed produce the same correction.

    Mutant #1358: 'rng is not None' → 'rng is None' — provided rng ignored,
    np.random.default_rng(None) used instead → likely different outputs each call.
    """
    seats = {f'P{i}': 1 for i in range(20)}
    quotas = _seats_to_quotas(seats)  # all 0

    result1 = correct_party_quotas(dict(quotas), seats, QuotaCorrectionStrategy.RANDOM,
                                   rng=np.random.default_rng(42))
    result2 = correct_party_quotas(dict(quotas), seats, QuotaCorrectionStrategy.RANDOM,
                                   rng=np.random.default_rng(42))

    assert result1 == result2


def test_random_strategy_selects_without_replacement():
    """RANDOM strategy must select each party at most once (replace=False).

    Mutant #1361: replace=False → replace=True — same party may be selected twice,
    giving quota > 1 for that party.
    20 parties with 1 seat each, deficit=10: pick 10 unique. With replace=True and
    seed=0 the chance of at least one duplicate is very high (>99.9%).
    """
    seats = {f'P{i}': 1 for i in range(20)}
    quotas = _seats_to_quotas(seats)  # all 0

    result = correct_party_quotas(dict(quotas), seats, QuotaCorrectionStrategy.RANDOM,
                                  seed=0)

    assert max(result.values()) <= 1, "A party was selected more than once (replace=True mutant)"
    assert sum(result.values()) == 10


# ---- PROPORTIONAL strategy: rng determinism and no duplicate selection ----

def test_proportional_strategy_is_deterministic_with_rng():
    """Two fresh rngs of the same seed produce the same correction.

    Mutant #1362: inverted rng check — provided rng ignored.
    """
    seats = {f'P{i}': 1 for i in range(20)}
    quotas = _seats_to_quotas(seats)

    result1 = correct_party_quotas(dict(quotas), seats, QuotaCorrectionStrategy.PROPORTIONAL,
                                   rng=np.random.default_rng(42))
    result2 = correct_party_quotas(dict(quotas), seats, QuotaCorrectionStrategy.PROPORTIONAL,
                                   rng=np.random.default_rng(42))

    assert result1 == result2


def test_proportional_strategy_selects_without_replacement():
    """PROPORTIONAL strategy must select each party at most once.

    Mutant #1368: replace=False → replace=True.
    """
    seats = {f'P{i}': 1 for i in range(20)}
    quotas = _seats_to_quotas(seats)

    result = correct_party_quotas(dict(quotas), seats, QuotaCorrectionStrategy.PROPORTIONAL,
                                  seed=0)

    assert max(result.values()) <= 1
    assert sum(result.values()) == 10


# ---- PROPORTIONAL_REVERSED strategy: rng determinism and no duplicate selection ----

def test_proportional_reversed_strategy_is_deterministic_with_rng():
    """Two fresh rngs of the same seed produce the same correction.

    Mutant #1369: inverted rng check — provided rng ignored.
    """
    seats = {f'P{i}': 1 for i in range(20)}
    quotas = _seats_to_quotas(seats)

    result1 = correct_party_quotas(dict(quotas), seats,
                                   QuotaCorrectionStrategy.PROPORTIONAL_REVERSED,
                                   rng=np.random.default_rng(42))
    result2 = correct_party_quotas(dict(quotas), seats,
                                   QuotaCorrectionStrategy.PROPORTIONAL_REVERSED,
                                   rng=np.random.default_rng(42))

    assert result1 == result2


def test_proportional_reversed_strategy_selects_without_replacement():
    """PROPORTIONAL_REVERSED strategy must select each party at most once.

    Mutant #1375: replace=False → replace=True.
    """
    seats = {f'P{i}': 1 for i in range(20)}
    quotas = _seats_to_quotas(seats)

    result = correct_party_quotas(dict(quotas), seats,
                                  QuotaCorrectionStrategy.PROPORTIONAL_REVERSED,
                                  seed=0)

    assert max(result.values()) <= 1
    assert sum(result.values()) == 10
