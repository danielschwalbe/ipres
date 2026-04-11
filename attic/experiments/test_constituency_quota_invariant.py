"""
Comprehensive test to verify the quota invariant:
In GOVERNING_MAJORITY mode, sum(quotas) must always equal number_of_constituencies.
"""

from ipres.election_config import ElectionConfig, ConstituencyRepresentation
from ipres.constituencies_config import ConstituenciesConfig
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit
import pandas as pd


def test_quota_invariant_comprehensive():
    """Test quota invariant across many parameter combinations."""

    print("="*80)
    print("COMPREHENSIVE TEST: Quota Invariant")
    print("="*80)
    print("\nInvariant: sum(quotas) = number_of_constituencies")
    print("Where: quotas = getParliamentMajoritySeats() // 2\n")

    # Test many combinations
    constituency_counts = [1, 10, 50, 100, 299, 500, 1000]
    percent_margins = [1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0]
    seats_margins = [1, 5, 10, 15, 20, 50, 100]

    all_pass = True
    test_count = 0
    fail_count = 0

    # Test PERCENT margins
    for constituencies in constituency_counts:
        for margin_value in percent_margins:
            test_count += 1
            margin = SuperMajorityMargin(margin_value, MarginUnit.PERCENT)

            # Create config
            constituencies_df = pd.DataFrame({
                'constituency_number': range(1, constituencies + 1),
                'constituency_name': [f'WK{i}' for i in range(1, constituencies + 1)],
                'constituency_size': [100000] * constituencies
            })
            constituencies_config = ConstituenciesConfig(constituencies_df)

            config = ElectionConfig(
                constituencies_config=constituencies_config,
                participating_parties=['A', 'B'],
                parliament_majority_margin=margin,
                constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
            )

            # Check invariant
            gov_seats = config.getParliamentMajoritySeats()
            quotas_sum = gov_seats // 2
            expected = constituencies

            if quotas_sum != expected:
                print(f"\n✗ FAIL: {constituencies} constituencies, {margin_value}% margin")
                print(f"  Gov seats: {gov_seats}, Quotas: {quotas_sum}, Expected: {expected}")
                all_pass = False
                fail_count += 1

    # Test SEATS margins (only for larger constituency counts)
    for constituencies in [c for c in constituency_counts if c >= 50]:
        for margin_value in [m for m in seats_margins if m < constituencies // 2]:
            test_count += 1
            margin = SuperMajorityMargin(margin_value, MarginUnit.SEATS)

            constituencies_df = pd.DataFrame({
                'constituency_number': range(1, constituencies + 1),
                'constituency_name': [f'WK{i}' for i in range(1, constituencies + 1)],
                'constituency_size': [100000] * constituencies
            })
            constituencies_config = ConstituenciesConfig(constituencies_df)

            config = ElectionConfig(
                constituencies_config=constituencies_config,
                participating_parties=['A', 'B'],
                parliament_majority_margin=margin,
                constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
            )

            gov_seats = config.getParliamentMajoritySeats()
            quotas_sum = gov_seats // 2
            expected = constituencies

            if quotas_sum != expected:
                print(f"\n✗ FAIL: {constituencies} constituencies, {margin_value} seats margin")
                print(f"  Gov seats: {gov_seats}, Quotas: {quotas_sum}, Expected: {expected}")
                all_pass = False
                fail_count += 1

    print(f"\nRan {test_count} tests")
    print(f"Failures: {fail_count}")

    print("\n" + "="*80)
    if all_pass:
        print("✓ ALL TESTS PASSED - Quota invariant holds!")
    else:
        print(f"✗ FAILED {fail_count}/{test_count} tests")
    print("="*80)

    return all_pass


if __name__ == "__main__":
    success = test_quota_invariant_comprehensive()
    exit(0 if success else 1)
