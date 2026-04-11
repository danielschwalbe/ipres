"""
Analyze whether governmentMajorityMarginSeats always equals 2 * number_of_constituencies
when constituency_representation == GOVERNING_MAJORITY.

This is required because quotas = seats // 2, and we need sum(quotas) == number_of_constituencies.
"""

import math
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit

def analyze_parliamentary_seats_calculation():
    """Analyze the relationship between constituencies, margin, and seats."""

    print("="*80)
    print("ANALYSIS: GOVERNING_MAJORITY Mode")
    print("="*80)

    print("\nREQUIREMENT:")
    print("  sum(quotas) = sum(seats // 2) = number_of_constituencies")
    print("  Therefore: sum(seats) must be EVEN and = 2 * number_of_constituencies")
    print()

    # Test various scenarios
    test_cases = [
        (299, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(10.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(15, MarginUnit.SEATS)),
        (299, SuperMajorityMargin(50, MarginUnit.SEATS)),
        (100, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (100, SuperMajorityMargin(7.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(2.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(3.3, MarginUnit.PERCENT)),
    ]

    print("TEST CASES:")
    print("-"*80)

    for constituencies, margin in test_cases:
        print(f"\nConstituencies: {constituencies}")
        print(f"Margin: {margin.value} {margin.unit.name}")

        if margin.unit == MarginUnit.PERCENT:
            # Formula: int(200 / (50 + margin.value) * constituencies)
            parliamentary_seats = int(200 / (50 + margin.value) * constituencies)
            formula = f"int(200 / (50 + {margin.value}) * {constituencies})"
        else:  # SEATS
            # Formula: constituencies * 4 - 2 * int(margin.value)
            parliamentary_seats = constituencies * 4 - 2 * int(margin.value)
            formula = f"{constituencies} * 4 - 2 * {int(margin.value)}"

        print(f"Formula: {formula}")
        print(f"Parliamentary Seats: {parliamentary_seats}")

        # Calculate governmentMajorityMarginSeats
        if margin.unit == MarginUnit.SEATS:
            margin_seats = int(margin.value)
        else:  # PERCENT
            margin_seats = math.ceil(parliamentary_seats * (margin.value / 100.0))

        print(f"GovernmentMajorityMarginSeats: {margin_seats}")

        # Check if even
        is_even = parliamentary_seats % 2 == 0
        print(f"Is Even: {is_even}")

        # Calculate expected vs actual
        expected_total_seats = 2 * constituencies
        actual_total_seats = parliamentary_seats

        print(f"Expected total seats (2 * constituencies): {expected_total_seats}")
        print(f"Actual total seats: {actual_total_seats}")

        # Check condition
        matches = actual_total_seats == expected_total_seats
        print(f"✓ MATCH" if matches else f"✗ MISMATCH (diff: {actual_total_seats - expected_total_seats})")

        if not matches:
            print(f"  → This means quotas won't sum to {constituencies}!")
            print(f"  → Actual quota sum will be: {actual_total_seats // 2}")


if __name__ == "__main__":
    analyze_parliamentary_seats_calculation()
