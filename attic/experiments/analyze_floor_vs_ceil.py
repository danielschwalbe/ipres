"""
Analyze what happens if we change getParliamentMajoritySeats() from ceil to floor.

CURRENT:
--------
getParliamentMajoritySeats() = ceil(percent * P / 100)

PROPOSED:
---------
getParliamentMajoritySeats() = floor(percent * P / 100)

QUESTION:
---------
1. Can we simplify the _get_parliamentary_seats calculation?
2. Will the invariant still hold?
3. What are the semantic implications?
"""

import math


def current_implementation(C, M_percent):
    """Current implementation with ceil."""
    # Calculate P
    P = int(200 * C / (50 + M_percent))

    # Adjust for ceil() rounding
    test_result = math.ceil((50 + M_percent) * P / 100)

    if test_result < 2 * C:
        P += 1
    elif test_result > 2 * C:
        P -= 1

    # Final government seats
    gov_seats = math.ceil((50 + M_percent) * P / 100)

    return P, gov_seats


def proposed_with_floor(C, M_percent):
    """Proposed implementation with floor."""
    # Calculate P - would we need adjustment?
    P = int(200 * C / (50 + M_percent))

    # With floor, what happens?
    test_result = math.floor((50 + M_percent) * P / 100)

    # Do we need adjustment?
    if test_result < 2 * C:
        P += 1
    elif test_result > 2 * C:
        P -= 1

    # Final government seats with floor
    gov_seats = math.floor((50 + M_percent) * P / 100)

    return P, gov_seats


def proposed_simplified(C, M_percent):
    """Could we simplify with floor?"""
    # With floor, maybe we can just use the formula directly?
    P = int(200 * C / (50 + M_percent))

    # No adjustment needed?
    gov_seats = math.floor((50 + M_percent) * P / 100)

    return P, gov_seats


def analyze_floor_vs_ceil():
    """Compare the three approaches."""

    print("="*80)
    print("ANALYSIS: floor vs ceil in getParliamentMajoritySeats()")
    print("="*80)

    test_cases = [
        (299, 5.0),
        (299, 10.0),
        (147, 28.4),  # Known problematic case
        (162, 36.4),  # Known problematic case
        (100, 7.5),
        (50, 2.5),
    ]

    print("\n" + "="*80)
    print("COMPARISON TABLE")
    print("="*80)
    print(f"{'C':<6} {'M%':<8} {'Current (ceil)':<20} {'Floor+adj':<20} {'Floor simple':<20}")
    print(f"{'':6} {'':8} {'P':<6} {'Gov':<6} {'Match':<6} {'P':<6} {'Gov':<6} {'Match':<6} {'P':<6} {'Gov':<6} {'Match':<6}")
    print("-"*80)

    for C, M in test_cases:
        expected = 2 * C

        # Current with ceil
        P_ceil, gov_ceil = current_implementation(C, M)
        match_ceil = "✓" if gov_ceil == expected else "✗"

        # Floor with adjustment
        P_floor_adj, gov_floor_adj = proposed_with_floor(C, M)
        match_floor_adj = "✓" if gov_floor_adj == expected else "✗"

        # Floor without adjustment
        P_floor_simple, gov_floor_simple = proposed_simplified(C, M)
        match_floor_simple = "✓" if gov_floor_simple == expected else "✗"

        print(f"{C:<6} {M:<8.1f} {P_ceil:<6} {gov_ceil:<6} {match_ceil:<6} "
              f"{P_floor_adj:<6} {gov_floor_adj:<6} {match_floor_adj:<6} "
              f"{P_floor_simple:<6} {gov_floor_simple:<6} {match_floor_simple:<6}")


def mathematical_analysis():
    """Analyze mathematically."""

    print("\n" + "="*80)
    print("MATHEMATICAL ANALYSIS")
    print("="*80)

    print("\nWith P = floor(200*C / (50+M)):")
    print("  P <= 200*C / (50+M) < P+1")
    print("  P*(50+M) <= 200*C < (P+1)*(50+M)")
    print("  P*(50+M)/100 <= 2*C < (P+1)*(50+M)/100")

    print("\nWith ceil():")
    print("  ceil(P*(50+M)/100) can be 2*C or 2*C+1")
    print("  → Need adjustment logic")

    print("\nWith floor():")
    print("  floor(P*(50+M)/100) <= 2*C")
    print("  But: floor(P*(50+M)/100) might be < 2*C")
    print("  → Still need adjustment logic!")

    print("\n" + "="*80)
    print("KEY INSIGHT")
    print("="*80)
    print("\nFrom P*(50+M) <= 200*C:")
    print("  floor(P*(50+M)/100) <= floor(200*C/100) = floor(2*C) = 2*C")
    print("\nBut we don't know if floor(P*(50+M)/100) = 2*C or < 2*C")
    print("So we still need the adjustment logic!")

    print("\nHowever, the 'P -= 1' branch would become impossible:")
    print("  floor() can never give us > 2*C (without floating-point errors)")


def semantic_implications():
    """Discuss semantic meaning."""

    print("\n" + "="*80)
    print("SEMANTIC IMPLICATIONS")
    print("="*80)

    print("\nceil(): Government majority means 'at least X%'")
    print("  - If 55% of 598 = 328.9, government needs 329 seats (rounds up)")
    print("  - Conservative: Ensures government definitely has the majority")
    print("  - Makes sense for 'majority threshold'")

    print("\nfloor(): Government majority means 'more than (X-ε)%'")
    print("  - If 55% of 598 = 328.9, government needs 328 seats (rounds down)")
    print("  - Liberal: Government might have slightly less than stated %")
    print("  - Actual percentage: 328/598 = 54.85% (< 55%)")

    print("\n→ Which is correct depends on interpretation!")
    print("  - Mathematical: 'at least X%' → use ceil()")
    print("  - Practical: 'approximately X%' → floor() might work")


if __name__ == "__main__":
    analyze_floor_vs_ceil()
    mathematical_analysis()
    semantic_implications()
