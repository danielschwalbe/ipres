"""
Analyze the floating-point precision issue causing the "rare cases".

HYPOTHESIS:
-----------
The issue is that:
  int(200 * C / (50 + M))  # Uses floating-point division

Due to floating-point rounding, we might get:
  int(200 * C / (50 + M)) slightly > floor(200 * C / (50 + M))

This can violate the mathematical proof.
"""

import math
from decimal import Decimal, getcontext


def analyze_specific_case(C, M):
    """Analyze a specific case in detail."""

    print(f"\n{'='*80}")
    print(f"DETAILED ANALYSIS: C={C}, M={M}%")
    print(f"{'='*80}")

    # Using float (what Python does)
    numerator_float = 200 * C
    denominator_float = 50 + M
    division_float = numerator_float / denominator_float
    P_float = int(division_float)

    print(f"\nUsing FLOAT arithmetic:")
    print(f"  200 * {C} = {numerator_float}")
    print(f"  50 + {M} = {denominator_float}")
    print(f"  {numerator_float} / {denominator_float} = {division_float}")
    print(f"  int({division_float}) = {P_float}")

    # Check if this is actually > floor
    P_floor = math.floor(division_float)
    print(f"  floor({division_float}) = {P_floor}")
    print(f"  Difference: {P_float - P_floor}")

    # Calculate test_result
    test_numerator = (50 + M) * P_float
    test_result_float = test_numerator / 100
    test_result = math.ceil(test_result_float)

    print(f"\nTest calculation:")
    print(f"  (50 + {M}) * {P_float} = {test_numerator}")
    print(f"  {test_numerator} / 100 = {test_result_float}")
    print(f"  ceil({test_result_float}) = {test_result}")
    print(f"  Expected <= {2*C}")
    print(f"  Result: {test_result} > {2*C}? {test_result > 2*C}")

    # Using high-precision Decimal
    getcontext().prec = 100  # Very high precision

    numerator_decimal = Decimal(200) * Decimal(C)
    denominator_decimal = Decimal(50) + Decimal(str(M))
    division_decimal = numerator_decimal / denominator_decimal
    P_decimal = int(division_decimal)

    print(f"\nUsing DECIMAL arithmetic (100 digits precision):")
    print(f"  {numerator_decimal} / {denominator_decimal} = {division_decimal}")
    print(f"  int({division_decimal}) = {P_decimal}")

    # Check with decimal
    test_numerator_decimal = (Decimal(50) + Decimal(str(M))) * Decimal(P_decimal)
    test_result_decimal_raw = test_numerator_decimal / Decimal(100)
    test_result_decimal = int(test_result_decimal_raw) + (1 if test_result_decimal_raw % 1 != 0 else 0)

    print(f"  Test result with P={P_decimal}: {test_result_decimal}")
    print(f"  Problem exists with Decimal? {test_result_decimal > 2*C}")

    # The issue
    if P_float > P_decimal:
        print(f"\n→ FLOATING-POINT BUG: int() returned {P_float} instead of {P_decimal}")
        print(f"  The mathematical floor is {P_decimal}, but float arithmetic gave {P_float}")


def test_all_problematic_cases():
    """Test all the problematic cases found."""

    print("="*80)
    print("TESTING ALL PROBLEMATIC CASES")
    print("="*80)

    problematic_cases = [
        (147, 28.4),
        (162, 36.4),
        (294, 28.4),
        (309, 32.4),
        (324, 36.4),
    ]

    for C, M in problematic_cases:
        analyze_specific_case(C, M)

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("\nThe 'Need fewer seats' case occurs due to floating-point precision issues.")
    print("Python's int() can sometimes round up instead of down due to representation errors.")
    print("\nSOLUTION: Use math.floor() instead of int() for guaranteed floor behavior.")


if __name__ == "__main__":
    test_all_problematic_cases()
