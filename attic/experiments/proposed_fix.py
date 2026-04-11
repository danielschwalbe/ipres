"""
Proposed fix for GOVERNING_MAJORITY parliamentary seats calculation.

PROBLEM:
--------
Current formulas calculate parliamentary_seats to ensure government has desired majority,
but ignore that we need: sum(quotas) = constituencies
where quotas = seats // 2

This means we need: parliamentary_seats to be chosen such that
sum(government_seats) // 2 = constituencies

SOLUTION:
---------
Work backwards from constituencies:
1. Fix total_seats = 2 * constituencies (so quotas sum correctly)
2. Calculate how many seats government gets
3. Verify government has required majority

FORMULAS:
---------
Let:
- C = number of constituencies
- M = margin (in percent or seats)
- P = parliamentary seats
- G = government seats (sum over government parties)

Current (WRONG):
  If margin in PERCENT:
    P = int(200 / (50 + M) * C)
  If margin in SEATS:
    P = C * 4 - 2 * M

Proposed (CORRECT):
  P = 2 * C  (ALWAYS)

  Then verify that government majority is achievable with this seat count.
  The margin specification becomes a VERIFICATION, not a calculation.
"""

import math
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit


def proposed_parliamentary_seats_calculation(
    number_of_constituencies: int,
    margin: SuperMajorityMargin
) -> int:
    """
    Calculate parliamentary seats for GOVERNING_MAJORITY mode.

    Always returns 2 * number_of_constituencies to ensure quotas work correctly.
    The margin is used later to verify government has sufficient majority.

    Args:
        number_of_constituencies: Number of constituencies
        margin: Desired government majority margin (informational)

    Returns:
        2 * number_of_constituencies (always)
    """
    return 2 * number_of_constituencies


def verify_government_majority(
    government_seats: int,
    parliamentary_seats: int,
    margin: SuperMajorityMargin
) -> tuple[bool, str]:
    """
    Verify if government has required majority.

    Args:
        government_seats: Seats won by government coalition
        parliamentary_seats: Total parliamentary seats
        margin: Required majority margin

    Returns:
        (is_valid, message): Tuple with validation result and explanation
    """
    actual_percent = 100.0 * government_seats / parliamentary_seats
    required_percent = 50.0 + (
        margin.value if margin.unit == MarginUnit.PERCENT
        else 100.0 * margin.value / parliamentary_seats
    )

    is_valid = actual_percent >= required_percent

    message = f"Government: {government_seats}/{parliamentary_seats} = {actual_percent:.2f}% "
    message += f"(required: {required_percent:.2f}%)"

    if is_valid:
        message += " ✓"
    else:
        message += f" ✗ (shortfall: {required_percent - actual_percent:.2f}%)"

    return is_valid, message


def test_proposed_solution():
    """Test the proposed solution."""
    print("="*80)
    print("PROPOSED SOLUTION TEST")
    print("="*80)

    test_cases = [
        (299, SuperMajorityMargin(5.0, MarginUnit.PERCENT), 164),  # Example: gov has 164/299 constituencies
        (100, SuperMajorityMargin(10.0, MarginUnit.PERCENT), 60),
        (50, SuperMajorityMargin(15, MarginUnit.SEATS), 30),
    ]

    for constituencies, margin, example_gov_constituencies in test_cases:
        print(f"\nConstituencies: {constituencies}")
        print(f"Margin: {margin.value} {margin.unit.name}")

        # Proposed calculation
        parliamentary_seats = proposed_parliamentary_seats_calculation(constituencies, margin)
        print(f"Parliamentary Seats: {parliamentary_seats}")

        # Example: government wins example_gov_constituencies
        government_seats = example_gov_constituencies * 2  # Each constituency = 2 seats
        print(f"Example Government Constituencies: {example_gov_constituencies}")
        print(f"Example Government Seats: {government_seats}")

        # Verify quotas
        total_quotas = parliamentary_seats // 2
        print(f"Total Quotas: {total_quotas}")
        print(f"Quotas match constituencies: {total_quotas == constituencies} ✓" if total_quotas == constituencies else f"✗")

        # Verify majority
        is_valid, message = verify_government_majority(government_seats, parliamentary_seats, margin)
        print(f"Majority check: {message}")


if __name__ == "__main__":
    test_proposed_solution()
