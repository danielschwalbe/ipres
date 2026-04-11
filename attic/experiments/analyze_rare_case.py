"""
Analyze when the "Need fewer seats (rare case)" can occur.

ALGORITHM:
----------
P = int(200 * C / (50 + M))  # Floor division
test_result = ceil((50 + M) * P / 100)

if test_result > 2*C:
    P -= 1  # "Need fewer seats"

QUESTION:
---------
Can ceil((50 + M) * P / 100) > 2*C when P = floor(200*C / (50 + M))?

ANALYSIS:
---------
Let P = floor(200*C / (50 + M))

Then: P <= 200*C / (50 + M) < P + 1

From the left inequality:
  P * (50 + M) <= 200*C
  (50 + M) * P / 100 <= 2*C
  ceil((50 + M) * P / 100) <= 2*C

So ceil((50 + M) * P / 100) can NEVER be > 2*C!

The "Need fewer seats" branch is IMPOSSIBLE with floor().

PROOF BY EXHAUSTIVE SEARCH:
----------------------------
Let's verify this empirically.
"""

import math


def analyze_rare_case():
    """Search for cases where we need fewer seats."""

    print("="*80)
    print("ANALYSIS: When does 'Need fewer seats' occur?")
    print("="*80)

    # Test exhaustively
    found_cases = []

    # Test various ranges
    for C in range(1, 1001):  # 1 to 1000 constituencies
        for M_times_10 in range(1, 500):  # 0.1% to 50% in 0.1% steps
            M = M_times_10 / 10.0

            # Calculate P using floor
            P = int(200 * C / (50 + M))

            # Check result
            test_result = math.ceil((50 + M) * P / 100)

            if test_result > 2 * C:
                found_cases.append((C, M, P, test_result))

    print(f"\nTested: 1-1000 constituencies, 0.1%-50% margins")
    print(f"Total tests: {1000 * 499} = 499,000")
    print(f"\nCases where test_result > 2*C: {len(found_cases)}")

    if found_cases:
        print("\n✗ FOUND CASES (should not happen):")
        for C, M, P, result in found_cases[:10]:  # Show first 10
            print(f"  C={C}, M={M}%, P={P}, result={result} (expected <= {2*C})")
    else:
        print("\n✓ NO CASES FOUND - The branch is indeed unreachable with floor()!")

    # Mathematical proof verification
    print("\n" + "="*80)
    print("MATHEMATICAL PROOF:")
    print("="*80)
    print("\nGiven: P = floor(200*C / (50 + M))")
    print("Then:  P <= 200*C / (50 + M)")
    print("       P * (50 + M) <= 200*C")
    print("       (50 + M) * P / 100 <= 2*C")
    print("       ceil((50 + M) * P / 100) <= 2*C")
    print("\nTherefore: test_result > 2*C is IMPOSSIBLE")
    print("="*80)

    # Check with ceiling instead
    print("\n" + "="*80)
    print("WHAT IF WE USED CEILING INSTEAD OF FLOOR?")
    print("="*80)

    ceiling_cases = []

    for C in range(1, 101):  # Smaller range for demo
        for M_times_10 in range(10, 200):  # 1% to 20%
            M = M_times_10 / 10.0

            # Calculate P using CEILING
            P = math.ceil(200 * C / (50 + M))

            # Check result
            test_result = math.ceil((50 + M) * P / 100)

            if test_result > 2 * C:
                ceiling_cases.append((C, M, P, test_result))

    print(f"\nWith ceil(): Found {len(ceiling_cases)} cases where test_result > 2*C")

    if ceiling_cases:
        print("\nExamples:")
        for C, M, P, result in ceiling_cases[:5]:
            print(f"  C={C}, M={M}%, P={P}, result={result} (expected {2*C})")
        print("\n→ This is why we use floor(), not ceil()!")


if __name__ == "__main__":
    analyze_rare_case()
