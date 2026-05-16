"""Party quotas correction module.

This module handles the correction of party quotas to ensure that:
    sum(quotas) == number_of_constituencies

The problem arises from integer division: sum(a_i // 2) <= sum(a_i) // 2
When each party's seats are divided by 2 individually, we lose one quota
for each party with an odd seat count.
"""

from __future__ import annotations
from typing import Optional, Any
import numpy as np
from numpy.random import Generator
from ipres.election_config import QuotaCorrectionStrategy

# ---------------------------------------------------------------------------------------------------------------------
def correct_party_quotas(quotas: dict[str, int], seats: dict[str, int], strategy : QuotaCorrectionStrategy,
    callback: Optional[callable] = None, rng: Optional[Generator] = None, seed: Optional[int] = None) -> dict[str, int]:
    """Correct party quotas to ensure sum(quotas) == sum(seats) // 2.
    Args:
        quotas: Dictionary of base quotas (seats // 2 per party)
        seats: Dictionary of seat counts per party
        strategy: QuotaCorrectionStrategy enum value
        callback: Optional callback for NEGOTIATED strategy
        rng: Optional random number generator for probabilistic strategies
        seed: Optional seed for creating RNG if rng is None
    Returns:
        Corrected quotas dictionary
    """
    # Calculate required total and current deficit
    total_seats = sum(seats.values())
    required_total_quotas = total_seats // 2
    current_quota_sum = sum(quotas.values())
    deficit = required_total_quotas - current_quota_sum

    # If there's no deficit, we're done
    if deficit <= 0:
        return quotas

    # Find parties with odd seat counts (candidates for +1)
    odd_seat_parties = {party: seats[party] for party in seats if seats[party] % 2 == 1}

    if len(odd_seat_parties) == 0:  # pragma: no mutate
        # Should never happen if deficit > 0, but safety check
        raise ValueError(f"Logical error somewhere: Deficit {deficit} > 0 but {len(odd_seat_parties)} == 0")  # pragma: no mutate

    # Select parties to receive +1 based on strategy
    parties_to_increment = select_parties_for_correction(odd_seat_parties, deficit, strategy, callback, rng, seed )

    # Apply corrections
    corrected_quotas = quotas.copy()
    for party in parties_to_increment:
        corrected_quotas[party] += 1

    return corrected_quotas
# ---------------------------------------------------------------------------------------------------------------------
def select_parties_for_correction(
    odd_seat_parties: dict[str, int],
    deficit: int,
    strategy,
    callback: Optional[callable] = None,
    rng: Optional[Generator] = None,
    seed: Optional[int] = None
) -> list[str]:
    """Select which parties with odd seats should receive +1 to their quota.

    Args:
        odd_seat_parties: Dictionary of parties with odd seat counts
        deficit: Number of +1 corrections needed
        strategy: QuotaCorrectionStrategy enum value
        callback: Optional callback for NEGOTIATED strategy
        rng: Optional random number generator for probabilistic strategies
        seed: Optional seed for creating RNG if rng is None

    Returns:
        List of party names to receive +1
    """
    if deficit > len(odd_seat_parties):  # pragma: no mutate
        raise ValueError(
            f"Deficit {deficit} exceeds number of parties with odd seats {len(odd_seat_parties)}"  # pragma: no mutate
        )

    if strategy == QuotaCorrectionStrategy.FAVOR_SMALL_PARTIES:
        # Sort by seat count ascending, take first 'deficit' parties
        return _favor_small_parties(deficit, odd_seat_parties)

    elif strategy == QuotaCorrectionStrategy.FAVOR_LARGE_PARTIES:
        # Sort by seat count descending, take first 'deficit' parties
        return _favor_large_parties(deficit, odd_seat_parties)

    elif strategy == QuotaCorrectionStrategy.RANDOM:
        # Uniform random selection
        return _select_random(deficit, odd_seat_parties, rng, seed)

    elif strategy == QuotaCorrectionStrategy.PROPORTIONAL:
        # Weighted by seat count (larger parties more likely)
        return _weighted_by_seat_count(deficit, odd_seat_parties, rng, seed)

    elif strategy == QuotaCorrectionStrategy.PROPORTIONAL_REVERSED:
        # Weighted by reversed proportions (smaller parties more likely)
        return _weighted_by_reversed_proportions(deficit, odd_seat_parties, rng, seed)

    elif strategy == QuotaCorrectionStrategy.NEGOTIATED:
        # Use callback to determine which parties receive +1
        if callback is None:
            raise ValueError("NEGOTIATED strategy requires quota_correction_callback")
        result = callback(odd_seat_parties, deficit)
        if not isinstance(result, (list, set)):
            raise ValueError("Callback must return a list or set of party names")
        if len(result) != deficit:
            raise ValueError(
                f"Callback must return exactly {deficit} parties, got {len(result)}"
            )
        return list(result)

    else:
        raise ValueError(f"Unknown quota correction strategy: {strategy}")  # pragma: no mutate

# -------------------------------------------------------------------------------------------------------------
def _favor_small_parties(deficit: int, odd_seat_parties: dict[str, int]) -> list[str]:
    """Select parties with the fewest seats to receive the quota correction."""
    sorted_parties = sorted(odd_seat_parties.items(), key=lambda x: x[1])
    return [party for party, _ in sorted_parties[:deficit]]


def _favor_large_parties(deficit: int, odd_seat_parties: dict[str, int]) -> list[str]:
    """Select parties with the most seats to receive the quota correction."""
    sorted_parties = sorted(odd_seat_parties.items(), key=lambda x: x[1], reverse=True)
    return [party for party, _ in sorted_parties[:deficit]]


def _select_random(deficit: int, odd_seat_parties: dict[str, int], rng: Generator | None, seed: int | None) -> list[
    Any]:
    """Uniformly randomly select parties to receive the quota correction."""
    actual_rng = rng if rng is not None else np.random.default_rng(seed)
    party_list = list(odd_seat_parties.keys())
    return list(actual_rng.choice(party_list, size=deficit, replace=False))


def _weighted_by_seat_count(deficit: int, odd_seat_parties: dict[str, int], rng: Generator | None, seed: int | None) -> list[Any]:
    """Probabilistically select parties weighted by seat count (larger parties more likely)."""
    actual_rng = rng if rng is not None else np.random.default_rng(seed)
    party_list = list(odd_seat_parties.keys())
    weights = np.array([odd_seat_parties[p] for p in party_list])
    probabilities = weights / weights.sum()
    return list(actual_rng.choice(party_list, size=deficit, replace=False, p=probabilities))


def _weighted_by_reversed_proportions(deficit: int, odd_seat_parties: dict[str, int], rng: Generator | None,
                                       seed: int | None) -> list[Any]:
    """Probabilistically select parties weighted by reversed proportions (smaller parties more likely)."""
    actual_rng = rng if rng is not None else np.random.default_rng(seed)
    party_list = list(odd_seat_parties.keys())
    weights = np.array([odd_seat_parties[p] for p in party_list])
    probabilities = weights / weights.sum()
    return list(actual_rng.choice(party_list, size=deficit, replace=False, p=probabilities[::-1]))
