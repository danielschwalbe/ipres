"""
Derive correct formula for GOVERNING_MAJORITY mode.

REQUIREMENT:
-----------
getParliamentMajoritySeats() = 2 * number_of_constituencies

This ensures government gets exactly the number of constituencies as quotas.

GIVEN:
------
getParliamentMajoritySeats() = ceil(getParliamentMajorityPercent() * parliamentary_seats / 100)
getParliamentMajorityPercent() = 50 + margin_percent

DERIVE:
-------
Let:
  C = number_of_constituencies
  P = parliamentary_seats
  M = margin (in percent)
  G = getParliamentMajoritySeats() = 2*C

From the formula:
  G = ceil((50 + M) * P / 100)

We want:
  ceil((50 + M) * P / 100) = 2*C

For simplicity, let's ensure:
  (50 + M) * P / 100 = 2*C  (exact, no ceiling needed)

Solve for P:
  P = 200*C / (50 + M)

Since P must be an integer, we need:
  P = round(200*C / (50 + M))

But we need to ensure the ceiling still gives us exactly 2*C.

Better approach: Work backwards from G = 2*C

If margin is in PERCENT:
  We need: ceil((50 + M) * P / 100) = 2*C

  For this to hold exactly without ceiling issues:
  P = 200*C / (50 + M)

  But since P must be integer, and we use ceil(), we need:
  (50 + M) * P / 100 >= 2*C
  (50 + M) * P / 100 < 2*C + 1

  From first inequality:
  P >= 200*C / (50 + M)

  From second:
  P < 100*(2*C + 1) / (50 + M)

  So:
  P = ceil(200*C / (50 + M))

If margin is in SEATS:
  margin_seats = M
  margin_percent = 100 * M / P

  getParliamentMajoritySeats() = ceil((50 + 100*M/P) * P / 100)
                                = ceil(P/2 + M)

  We want:
  ceil(P/2 + M) = 2*C

  For exact match (no ceiling issues):
  P/2 + M = 2*C
  P = 2*(2*C - M)
  P = 4*C - 2*M
"""

import math
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit


def calculate_parliamentary_seats_correct(
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
        # P = ceil(200*C / (50 + M))
        P = math.ceil(200 * C / (50 + M))
    else:  # SEATS
        M = int(margin.value)
        # P = 4*C - 2*M
        P = 4 * C - 2 * M

    return P


def calculate_government_majority_seats(parliamentary_seats: int, margin: SuperMajorityMargin) -> int:
    """
    Calculate government majority seats (mimics getParliamentMajoritySeats()).

    Args:
        parliamentary_seats: Total parliamentary seats
        margin: Majority margin

    Returns:
        Number of seats for government majority
    """
    if margin.unit == MarginUnit.PERCENT:
        percent = 50.0 + margin.value
    else:  # SEATS
        margin_seats = int(margin.value)
        percent = 50.0 + 100.0 * margin_seats / parliamentary_seats

    return math.ceil(percent * parliamentary_seats / 100.0)


def test_correct_formula():
    """Test the corrected formula."""
    print("="*80)
    print("CORRECTED FORMULA TEST")
    print("="*80)
    print("\nREQUIREMENT: getParliamentMajoritySeats() = 2 * number_of_constituencies\n")

    test_cases = [
        (299, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(10.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(15, MarginUnit.SEATS)),
        (299, SuperMajorityMargin(50, MarginUnit.SEATS)),
        (100, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (100, SuperMajorityMargin(7.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(2.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(5, MarginUnit.SEATS)),
    ]

    all_pass = True

    for constituencies, margin in test_cases:
        print(f"\nConstituencies: {constituencies}")
        print(f"Margin: {margin.value} {margin.unit.name}")

        # Calculate seats
        parliamentary_seats = calculate_parliamentary_seats_correct(constituencies, margin)
        print(f"Parliamentary Seats: {parliamentary_seats}")

        # Calculate government majority seats
        gov_majority_seats = calculate_government_majority_seats(parliamentary_seats, margin)
        print(f"Government Majority Seats: {gov_majority_seats}")

        # Expected
        expected = 2 * constituencies
        print(f"Expected (2 * constituencies): {expected}")

        # Check
        match = gov_majority_seats == expected
        print(f"Match: {match} {'✓' if match else '✗'}")

        if not match:
            print(f"  ERROR: Difference = {gov_majority_seats - expected}")
            all_pass = False

        # Also verify quotas
        total_quotas = gov_majority_seats // 2
        quota_match = total_quotas == constituencies
        print(f"Quotas (gov_majority_seats // 2): {total_quotas}")
        print(f"Quota match: {quota_match} {'✓' if quota_match else '✗'}")

        if not quota_match:
            all_pass = False

    print("\n" + "="*80)
    if all_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80)


if __name__ == "__main__":
    test_correct_formula()
