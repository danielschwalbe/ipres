"""Tests for SuperMajorityMargin validation."""

import dataclasses
import pytest
from ipres.super_majority_margin import SuperMajorityMargin, MarginUnit


def test_seats_unit_distinct_from_percent():
    """MarginUnit.SEATS must be a distinct member from MarginUnit.PERCENT.

    Mutant #57 sets PERCENT = 2, which collides with SEATS = 2 and makes SEATS
    an alias for PERCENT. With that alias every SEATS margin is validated against
    the [0, 100] percent rule, so a large seat count (e.g. 200) raises ValueError
    even though it is a perfectly valid number of seats.

    200 seats is non-negative and an integer, so construction must succeed.
    """
    margin = SuperMajorityMargin(200, MarginUnit.SEATS)
    assert margin.value == 200
    assert margin.unit == MarginUnit.SEATS


def test_super_majority_margin_is_frozen():
    """SuperMajorityMargin is a frozen dataclass; post-construction writes must fail.

    Mutant #61 changes frozen=True to frozen=False, allowing attribute assignment.
    Construction with value=5, unit=PERCENT must succeed, and any subsequent
    write must raise FrozenInstanceError.
    """
    margin = SuperMajorityMargin(5.0, MarginUnit.PERCENT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        margin.value = 10.0  # type: ignore[misc]


def test_percent_margin_boundary_100_valid():
    """value=100 is the maximum valid percent margin; value=101 must be rejected.

    Mutant #67 changes <= 100 to < 100, making value=100 invalid.
    Mutant #68 changes <= 100 to <= 101, making value=101 valid.

    100% margin: boundary value, must construct without error.
    101% margin: above maximum, must raise ValueError.
    """
    margin = SuperMajorityMargin(100.0, MarginUnit.PERCENT)
    assert margin.value == 100.0

    with pytest.raises(ValueError):
        SuperMajorityMargin(101.0, MarginUnit.PERCENT)


def test_zero_seat_margin_is_valid():
    """A seat margin of 0 is valid (means simple majority, no extra seats required).

    Mutant #70 changes < 0 to <= 0, rejecting value=0.
    Mutant #71 changes < 0 to < 1, also rejecting value=0.

    0 seats is non-negative, so construction must succeed.
    """
    margin = SuperMajorityMargin(0, MarginUnit.SEATS)
    assert margin.value == 0


def test_non_integer_float_seat_margin_rejected_integer_float_accepted():
    """Non-integer float seat values must be rejected; integer-valued floats are accepted.

    Mutant #73 inverts isinstance, allowing 1.5 (non-integer float) without error.
    Mutant #74 inverts is_integer(), rejecting 2.0 (integer float) and accepting 1.5.
    Mutant #75 uses 'or' instead of 'and', rejecting 2.0.

    value=1.5, unit=SEATS: not a whole number → ValueError.
    value=2.0, unit=SEATS: equals integer 2 → valid, must construct without error.
    """
    with pytest.raises(ValueError):
        SuperMajorityMargin(1.5, MarginUnit.SEATS)

    margin = SuperMajorityMargin(2.0, MarginUnit.SEATS)
    assert margin.value == 2.0
