"""
Fix the ceiling issue for PERCENT margin.

PROBLEM:
--------
When using ceil(), we get:
  ceil((50 + M) * P / 100) = 2*C + 1  (instead of 2*C)

SOLUTION:
---------
Instead of: P = ceil(200*C / (50 + M))
Use:        P = floor(200*C / (50 + M))  or  int(200*C / (50 + M))

But we need to ensure ceil((50 + M) * P / 100) = 2*C

Let's verify: If P = floor(200*C / (50 + M)), then:
  (50 + M) * P / 100 <= 2*C
  ceil((50 + M) * P / 100) <= 2*C

We want it to equal 2*C, so we need to ensure:
  (50 + M) * P / 100 > 2*C - 1

Actually, let's work backwards more carefully:

We want: ceil((50 + M) * P / 100) = 2*C

This means: 2*C - 1 < (50 + M) * P / 100 <= 2*C

From right inequality:
  P <= 200*C / (50 + M)

From left inequality:
  P > 100*(2*C - 1) / (50 + M)
  P > (200*C - 100) / (50 + M)

So P must satisfy:
  (200*C - 100) / (50 + M) < P <= 200*C / (50 + M)

The largest integer P satisfying this is:
  P = floor(200*C / (50 + M))

UNLESS floor(200*C / (50 + M)) <= floor((200*C - 100) / (50 + M))

In which case we need:
  P = floor(200*C / (50 + M)) + 1

Actually, simpler approach: Try P = floor(200*C / (50 + M)), check if it works,
if not, increment.
"""

import math
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit


def calculate_parliamentary_seats_fixed(
    number_of_constituencies: int,
    margin: SuperMajorityMargin
) -> int:
    """
    Calculate parliamentary seats ensuring getParliamentMajoritySeats() = 2 * constituencies.

    Args:
        number_of_constituencies: Number of constituencies
        margin: Government majority margin

    Returns:
        Parliamentary seats
    """
    C = number_of_constituencies

    if margin.unit == MarginUnit.PERCENT:
        M = margin.value
        # Start with floor, then adjust if needed
        P = int(200 * C / (50 + M))

        # Check if this gives us the right result
        test_result = math.ceil((50 + M) * P / 100)

        if test_result < 2 * C:
            # Need more seats
            P += 1
        elif test_result > 2 * C:
            # Need fewer seats (shouldn't happen with floor, but check)
            P -= 1

    else:  # SEATS
        M = int(margin.value)
        P = 4 * C - 2 * M

    return P


def calculate_government_majority_seats(parliamentary_seats: int, margin: SuperMajorityMargin) -> int:
    """
    Calculate government majority seats (mimics getParliamentMajoritySeats()).
    """
    if margin.unit == MarginUnit.PERCENT:
        percent = 50.0 + margin.value
    else:  # SEATS
        margin_seats = int(margin.value)
        percent = 50.0 + 100.0 * margin_seats / parliamentary_seats

    return math.ceil(percent * parliamentary_seats / 100.0)


def test_fixed_formula():
    """Test the fixed formula."""
    print("="*80)
    print("FIXED FORMULA TEST")
    print("="*80)
    print("\nREQUIREMENT: getParliamentMajoritySeats() = 2 * number_of_constituencies\n")

    test_cases = [
        (299, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(10.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(2.5, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(15, MarginUnit.SEATS)),
        (299, SuperMajorityMargin(50, MarginUnit.SEATS)),
        (100, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (100, SuperMajorityMargin(7.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(2.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(5, MarginUnit.SEATS)),
        (1, SuperMajorityMargin(1.0, MarginUnit.PERCENT)),  # Edge case
    ]

    all_pass = True

    for constituencies, margin in test_cases:
        print(f"\nConstituencies: {constituencies}, Margin: {margin.value} {margin.unit.name}")

        # Calculate seats
        parliamentary_seats = calculate_parliamentary_seats_fixed(constituencies, margin)
        print(f"  Parliamentary Seats: {parliamentary_seats}")

        # Calculate government majority seats
        gov_majority_seats = calculate_government_majority_seats(parliamentary_seats, margin)
        print(f"  Government Majority Seats: {gov_majority_seats}")

        # Expected
        expected = 2 * constituencies
        print(f"  Expected: {expected}")

        # Check
        match = gov_majority_seats == expected
        status = '✓' if match else '✗'
        print(f"  Match: {status}")

        if not match:
            print(f"    ERROR: Difference = {gov_majority_seats - expected}")
            all_pass = False

        # Verify quotas
        total_quotas = gov_majority_seats // 2
        quota_match = total_quotas == constituencies
        if not quota_match:
            print(f"    QUOTA ERROR: {total_quotas} != {constituencies}")
            all_pass = False

    print("\n" + "="*80)
    if all_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80)


if __name__ == "__main__":
    test_fixed_formula()
