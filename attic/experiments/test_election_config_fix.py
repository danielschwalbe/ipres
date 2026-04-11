"""Test that the fix in election_config.py works correctly."""

from ipres.election_config import ElectionConfig, ConstituencyRepresentation
from ipres.constituencies_config import ConstituenciesConfig
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit
import pandas as pd


def test_government_majority_seats():
    """Test that getParliamentMajoritySeats() = 2 * constituencies."""

    test_cases = [
        (299, SuperMajorityMargin(5.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(10.0, MarginUnit.PERCENT)),
        (299, SuperMajorityMargin(15, MarginUnit.SEATS)),
        (100, SuperMajorityMargin(7.5, MarginUnit.PERCENT)),
        (50, SuperMajorityMargin(5, MarginUnit.SEATS)),
    ]

    print("="*80)
    print("TEST: ElectionConfig GOVERNING_MAJORITY Fix")
    print("="*80)

    all_pass = True

    for num_constituencies, margin in test_cases:
        # Create constituencies
        constituencies_df = pd.DataFrame({
            'constituency_number': range(1, num_constituencies + 1),
            'constituency_name': [f'WK{i}' for i in range(1, num_constituencies + 1)],
            'constituency_size': [100000] * num_constituencies
        })
        constituencies_config = ConstituenciesConfig(constituencies_df)

        # Create election config
        config = ElectionConfig(
            constituencies_config=constituencies_config,
            participating_parties=['A', 'B', 'C'],
            parliament_majority_margin=margin,
            constituency_representation=ConstituencyRepresentation.GOVERNING_MAJORITY
        )

        print(f"\n{num_constituencies} constituencies, Margin: {margin.value} {margin.unit.name}")
        print(f"  Parliamentary Seats: {config.parliamentarySeats}")
        print(f"  Government Majority Seats: {config.getParliamentMajoritySeats()}")
        print(f"  Expected: {2 * num_constituencies}")

        # Check
        expected = 2 * num_constituencies
        actual = config.getParliamentMajoritySeats()
        match = actual == expected

        if match:
            print(f"  ✓ PASS")
        else:
            print(f"  ✗ FAIL (difference: {actual - expected})")
            all_pass = False

        # Also verify quota logic
        quotas_sum = config.getParliamentMajoritySeats() // 2
        quota_match = quotas_sum == num_constituencies
        print(f"  Quotas sum: {quotas_sum} (should be {num_constituencies}) {'✓' if quota_match else '✗'}")

        if not quota_match:
            all_pass = False

    print("\n" + "="*80)
    if all_pass:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*80)

    return all_pass


if __name__ == "__main__":
    success = test_government_majority_seats()
    exit(0 if success else 1)
