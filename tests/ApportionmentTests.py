"""
Unit tests for seat apportionment methods.

These tests verify the three main proportional representation methods:
1. Sainte-Laguë/Schepers (divisor method with odd divisors: 1, 3, 5, 7, ...)
2. D'Hondt (divisor method with natural divisors: 1, 2, 3, 4, ...)
3. Hare-Niemeyer (largest remainder method)

Sources:
- Sainte-Laguë: https://en.wikipedia.org/wiki/Sainte-Lagu%C3%AB_method
- D'Hondt: https://en.wikipedia.org/wiki/D%27Hondt_method
- Hare-Niemeyer: https://en.wikipedia.org/wiki/Largest_remainder_method
"""

import pytest
import numpy as np
from ipres.apportionment import apportionSeats
from ipres import SeatDistributionMethod


def test_simple_two_party_dhondt():
    """
    D'Hondt method test with 2 parties.

    Parties: A=100 votes, B=200 votes (total=300)
    Seats: 10

    Manual calculation:
    A: 100/1=100, 100/2=50, 100/3=33.3, 100/4=25
    B: 200/1=200, 200/2=100, 200/3=66.7, 200/4=50, 200/5=40

    Top 10 quotients (in descending order):
    1. B/1=200 -> B gets seat 1
    2. A/1=100 -> A gets seat 1
    3. B/2=100 -> B gets seat 2
    4. B/3=66.7 -> B gets seat 3
    5. A/2=50 -> A gets seat 2
    6. B/4=50 -> B gets seat 4
    7. B/5=40 -> B gets seat 5
    8. A/3=33.3 -> A gets seat 3
    9. A/4=25 -> (if we had 11 seats)
    10. B/6=33.3 -> (if we had 11 seats)

    Wait, let me recalculate more carefully:
    Top 10: 200, 100, 100, 66.7, 50, 50, 40, 33.3, 33.3, 25

    Assignment:
    200(B), 100(A), 100(B), 66.7(B), 50(A), 50(B), 40(B), 33.3(A), 33.3(B), 25(A)?

    Actually, when quotients tie, we need tie-breaking. But with these numbers:
    Top 10 quotients: 200(B), 100(B), 100(A), 66.7(B), 50(B), 50(A), 40(B), 33.3(B), 33.3(A), 25(A)

    Result: A gets 3 seats, B gets 7 seats
    """
    votes = np.array([100, 200])
    seats = apportionSeats(votes, 10, SeatDistributionMethod.D_HONDT)
    assert seats[0] == 3  # Party A
    assert seats[1] == 7  # Party B
    assert seats.sum() == 10


def test_simple_two_party_sainte_lague():
    """
    Sainte-Laguë method test with 2 parties.

    Parties: A=100 votes, B=200 votes
    Seats: 10

    Manual calculation (divisors: 1, 3, 5, 7, 9, ...):
    A: 100/1=100, 100/3=33.3, 100/5=20, 100/7=14.3
    B: 200/1=200, 200/3=66.7, 200/5=40, 200/7=28.6, 200/9=22.2

    Top 10 quotients:
    1. 200(B) -> B gets seat 1
    2. 100(A) -> A gets seat 1
    3. 66.7(B) -> B gets seat 2
    4. 40(B) -> B gets seat 3
    5. 33.3(A) -> A gets seat 2
    6. 28.6(B) -> B gets seat 4
    7. 22.2(B) -> B gets seat 5
    8. 20(A) -> A gets seat 3
    9. 14.3(A) -> (if we had 11 seats)
    10. ?

    Wait, we need 10 seats. Let me recalculate:
    Quotients: 200, 100, 66.7, 40, 33.3, 28.6, 22.2, 20, 14.3, 11.1(B)

    Result: A gets 3 seats, B gets 7 seats
    """
    votes = np.array([100, 200])
    seats = apportionSeats(votes, 10, SeatDistributionMethod.SAINTE_LAGUE)
    assert seats[0] == 3  # Party A
    assert seats[1] == 7  # Party B
    assert seats.sum() == 10


def test_simple_two_party_hare_niemeyer():
    """
    Hare-Niemeyer (largest remainder) method test.

    Parties: A=100 votes, B=200 votes (total=300)
    Seats: 10

    Quota = 300 / 10 = 30
    A: 100 / 30 = 3.333... -> floor = 3, remainder = 10
    B: 200 / 30 = 6.666... -> floor = 6, remainder = 20

    Assigned so far: 3 + 6 = 9 seats
    Remaining: 1 seat

    Largest remainder is B (20), so B gets the extra seat.

    Result: A gets 3 seats, B gets 7 seats

    Actually wait: remainder = votes - (floor * quota)
    A: 100 - (3 * 30) = 100 - 90 = 10
    B: 200 - (6 * 30) = 200 - 180 = 20

    Yep, B gets the extra seat.
    Final: A=3, B=7?

    Hmm, let me recalculate: 3 + 7 = 10, but we assigned 9 + 1 = 10.
    So A=3, B=6+1=7. But wait, the original floor sum was 9, so we give 1 to highest remainder.

    Actually for proportionality: A should get 100/300 * 10 = 3.33, B should get 200/300 * 10 = 6.67
    So probably A=3 or 4, B=7 or 6 depending on rounding.

    With Hare-Niemeyer and quota=30: A gets floor(3.33)=3, B gets floor(6.67)=6, then 1 remainder to B.
    Final: A=3, B=7? No wait, that's 10 total but we said sum of floors was 9...

    Let me be more careful:
    floor(100/30) = floor(3.333) = 3
    floor(200/30) = floor(6.666) = 6
    Sum = 9, need 10, so 1 remaining

    Remainders: A=100-90=10, B=200-180=20
    B has larger remainder, so B gets +1
    Final: A=3, B=7 ✓

    But proportionally A/300 = 33.3%, B/300 = 66.7%
    A=3/10 = 30%, B=7/10 = 70%
    Close but not perfect.

    Actually, better test: A=4, B=6 would give 40% and 60%. Let me check:
    If we give the extra seat to A instead: A=4, B=6
    A: 4/10 = 40% (should be 33.3%)
    B: 6/10 = 60% (should be 66.7%)

    This is worse! So A=3, B=7 is correct.
    """
    votes = np.array([100, 200])
    seats = apportionSeats(votes, 10, SeatDistributionMethod.HARE_NIEMEYER)

    # The proportional shares are 33.3% and 66.7%
    # With 10 seats, this rounds to 3 and 7
    # But depending on rounding, could be 4 and 6
    # Let's check what we actually get and verify it sums to 10
    assert seats.sum() == 10

    # For these specific votes, A should get 3-4 seats, B should get 6-7 seats
    assert 3 <= seats[0] <= 4
    assert 6 <= seats[1] <= 7

    # More precisely: quota = 30, so A=3.33, B=6.67
    # floors: A=3, B=6, sum=9, give 1 to largest remainder
    # A remainder = 10, B remainder = 20, so B gets it
    assert seats[0] == 3
    assert seats[1] == 7


def test_three_party_example():
    """Test with 3 parties to ensure all methods work."""
    votes = np.array([100, 200, 150])
    seats_total = 15

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        assert seats.sum() == seats_total, f"Method {method.name} didn't allocate all seats"
        assert all(s >= 0 for s in seats), f"Method {method.name} gave negative seats"


def test_equal_votes():
    """Test with equal votes - each party should get equal seats."""
    votes = np.array([100, 100, 100])
    seats_total = 9

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        assert seats.sum() == seats_total
        # With equal votes, each should get 3 seats
        assert all(s == 3 for s in seats), f"Method {method.name} didn't distribute equally"


def test_zero_votes():
    """Test party with zero votes gets zero seats."""
    votes = np.array([100, 0, 200])
    seats_total = 10

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        assert seats[1] == 0, f"Method {method.name} gave seats to party with 0 votes"
        assert seats.sum() == seats_total


def test_all_zero_votes():
    """Test with all parties having zero votes."""
    votes = np.array([0, 0, 0])
    seats_total = 10

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        # Should return all zeros
        assert all(s == 0 for s in seats)


def test_zero_seats():
    """Test with zero seats to distribute."""
    votes = np.array([100, 200])
    seats_total = 0

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        assert all(s == 0 for s in seats)


def test_single_seat():
    """Test with only 1 seat - should go to party with most votes."""
    votes = np.array([100, 200, 50])
    seats_total = 1

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        assert seats.sum() == 1
        assert seats[1] == 1, f"Method {method.name} didn't give single seat to party with most votes"


def test_dhondt_favors_larger_parties():
    """
    D'Hondt is known to favor larger parties compared to Sainte-Laguë.
    Test this property.
    """
    votes = np.array([40, 30, 20, 10])
    seats_total = 10

    dhondt = apportionSeats(votes, seats_total, SeatDistributionMethod.D_HONDT)
    sainte = apportionSeats(votes, seats_total, SeatDistributionMethod.SAINTE_LAGUE)

    # D'Hondt should give more seats to the largest party
    # and fewer to the smallest parties compared to Sainte-Laguë
    assert dhondt[0] >= sainte[0], "D'Hondt should favor largest party"


def test_consistency_across_methods():
    """All methods should allocate exactly the right number of seats."""
    test_cases = [
        (np.array([100, 200, 150]), 15),
        (np.array([50, 50, 50, 50]), 20),
        (np.array([1000, 500, 250]), 30),
        (np.array([42, 35, 23]), 100),
    ]

    for votes, seats_total in test_cases:
        for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
            seats = apportionSeats(votes, seats_total, method)
            assert seats.sum() == seats_total, \
                f"Method {method.name} with votes {votes} didn't sum to {seats_total}"
            assert all(s >= 0 for s in seats), \
                f"Method {method.name} with votes {votes} gave negative seats"


def test_sainte_lague_exact_seat_allocation():
    # Distinguishes correct divisors (1,3,5,...) from (1,4,7,...): with votes=[100,18]
    # and P=3, quotients 100 > 33.3 > 20 > 18 give A all 3 seats; mutated divisors
    # produce 100 > 25 > 18, which gives A only 2 seats.
    seats = apportionSeats([100, 18], 3, SeatDistributionMethod.SAINTE_LAGUE)
    assert np.array_equal(seats, [3, 0])


def test_hare_niemeyer_tiebreaker_larger_votes_wins():
    """When remainders tie, the party with more votes receives the extra seat."""
    # votes=[6,4,2], P=3, quota=4: A base=1 rem=2, B base=1 rem=0, C base=0 rem=2.
    # A and C tie on remainder; A wins because it has more votes (6 > 2).
    seats = apportionSeats([6, 4, 2], 3, SeatDistributionMethod.HARE_NIEMEYER)
    assert np.array_equal(seats, [2, 1, 0])


def test_hare_niemeyer_extra_seat_by_largest_remainder():
    """The extra seat must go to the party with the largest fractional remainder."""
    # votes=[3,2,1], P=2, quota=3: A base=1 rem=0, B base=0 rem=2, C base=0 rem=1.
    # B has the largest remainder and receives the single extra seat.
    seats = apportionSeats([3, 2, 1], 2, SeatDistributionMethod.HARE_NIEMEYER)
    assert np.array_equal(seats, [1, 1, 0])


def test_proportionality():
    """Test that seat percentages roughly match vote percentages."""
    votes = np.array([1000, 2000, 3000])
    seats_total = 100

    vote_pct = votes / votes.sum() * 100

    for method in [SeatDistributionMethod.SAINTE_LAGUE, SeatDistributionMethod.D_HONDT, SeatDistributionMethod.HARE_NIEMEYER]:
        seats = apportionSeats(votes, seats_total, method)
        seat_pct = seats / seats.sum() * 100

        # Check that seat percentages are within reasonable range of vote percentages
        for i in range(len(votes)):
            diff = abs(seat_pct[i] - vote_pct[i])
            assert diff < 2.0, \
                f"Method {method.name}: Party {i} seat% ({seat_pct[i]:.1f}) differs from vote% ({vote_pct[i]:.1f}) by {diff:.1f}"
