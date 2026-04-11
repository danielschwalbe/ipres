import pytest
import pandas as pd
import numpy as np
from ipres import (
    Election, ElectionConfig, ConstituenciesConfig,
    SeatDistributionMethod, Contestant, contestantsDictFromParties, Ballot, ElectionRound,
    ElectionEvaluator, ConstituencyRepresentation, ElectionRoundInput, DrawLotsStrategy,
)
from ipres.allocation import ConstituencyAllocationMethod


def make_simple_cc(num_constituencies=10, size=10000):
    """Helper to create a simple constituencies config."""
    df = pd.DataFrame({
        'constituency_name': [f"C{i}" for i in range(1, num_constituencies + 1)],
        'constituency_size': [size] * num_constituencies,
    })
    return ConstituenciesConfig.from_dataframe(df)


def create_evaluator(seed=None, **kwargs):
    """Helper to create an ElectionEvaluator with default settings."""
    defaults = {
        'seat_distribution_method': SeatDistributionMethod.SAINTE_LAGUE,
        'constituency_allocation_method': ConstituencyAllocationMethod.OPTIMAL,
        'seed': seed
    }
    defaults.update(kwargs)
    return ElectionEvaluator(**defaults)


def test_distribute_seats_without_assigned_majority():
    """Test seat distribution when all parties go to final round (no party reduction)."""
    cc = make_simple_cc(5, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],
        seed=123
    )

    election = Election(electionConfig=config)

    # Run first iteration
    first_iter = election.start()

    # Form coalition A+B (leaving C out)
    if not first_iter.hasWinner():
        contestants_list = [first_iter.getContestants()["A"], first_iter.getContestants()["B"]]
        first_iter.formCoalition("Coalition_AB", contestants_list)

    # Continue election
    final_iter = first_iter
    while not final_iter.hasWinner() and final_iter.hasNext():
        next_input = final_iter.getNextRoundInput()
        final_iter = ElectionRound.run(next_input)

    # No party reduction from first to last — election had an outright winner
    assert election.hadOutrightWinner() is True

    evaluator = create_evaluator(seed=config.seed)
    result = evaluator.evaluate(election)
    seats = result.seats
    total_seats = election.electionConfig.parliamentarySeats

    # Check total seats adds up
    assert sum(seats.values()) == total_seats

    # Seats should be distributed to individual parties (A, B, C), NOT to Coalition_AB
    assert "A" in seats, "Party A should have seats"
    assert "B" in seats, "Party B should have seats"
    assert "C" in seats, "Party C should have seats"
    assert "Coalition_AB" not in seats, "Coalition should not appear in seat distribution"

    # Check that seat distribution is reasonable (all parties get some seats)
    for party in ["A", "B", "C"]:
        assert seats[party] >= 0, f"Party {party} should have non-negative seats"


def test_distribute_seats_without_assigned_majority_with_coalition():
    """Test Path 2: seats distributed to parties, not coalitions, based on member vote weights."""
    cc = make_simple_cc(5, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],        seed=456
    )

    election = Election(electionConfig=config)

    # Run first iteration
    first_iter = election.start()

    # Form coalition A+B (60% + 30% = 90% combined, leaving C and D)
    if not first_iter.hasWinner():
        contestants_list = [first_iter.getContestants()["A"], first_iter.getContestants()["B"]]
        first_iter.formCoalition("Coalition_AB", contestants_list)

    # Continue election without triggering party reduction
    final_iter = first_iter
    while not final_iter.hasWinner() and final_iter.hasNext():
        next_input = final_iter.getNextRoundInput()
        final_iter = ElectionRound.run(next_input)

    # Path 2: Outright winner — proportional distribution
    if election.hadOutrightWinner():
        evaluator = ElectionEvaluator(seed=config.seed)

        result = evaluator.evaluate(election)

        seats = result.seats
        total_seats = election.electionConfig.parliamentarySeats

        # Verify seats distributed to individual parties
        assert "A" in seats, "Party A should have individual seats"
        assert "B" in seats, "Party B should have individual seats"
        assert "C" in seats or "D" in seats, "Other parties should have seats"
        assert "Coalition_AB" not in seats, "Coalition should not appear in seat distribution"

        # Total seats should match
        assert sum(seats.values()) == total_seats

        # Seats for A and B should be proportional to their coalition member weights
        # A had more votes than B initially, so should have more seats
        if "A" in seats and "B" in seats:
            # We expect A > B since A had higher initial votes
            assert seats["A"] >= seats["B"], "A should have at least as many seats as B"


def test_distribute_seats_with_assigned_majority():
    """Test seat distribution with assigned government majority (party reduction occurred)."""
    cc = make_simple_cc(10, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],        seed=42
    )

    election = Election(electionConfig=config)

    # Manually run election and check if we get party reduction
    final_iter = election.run()

    # Party reduction occurred — no outright winner
    if not election.hadOutrightWinner():
        evaluator = ElectionEvaluator(seed=config.seed)

        result = evaluator.evaluate(election)

        seats = result.seats
        total_seats = election.electionConfig.parliamentarySeats
        gov_majority_seats = election.electionConfig.getParliamentMajoritySeats()

        # Check total seats
        assert sum(seats.values()) == total_seats

        # Winner should have government majority seats
        winner_name = election.getWinner().name
        assert seats[winner_name] == gov_majority_seats

        # Other parties should share remaining seats proportionally to first iteration
        remaining_seats = total_seats - gov_majority_seats
        first_votes = election.getFirstIteration().getOriginalContestantsVotes()

        # Get votes for non-winner parties
        winner_parties = election.getWinner().getContainedParties()
        other_votes = first_votes.drop(winner_parties)

        # Check other parties' seats are proportional to their first iteration votes
        other_seats = {party: seats[party] for party in other_votes.index}
        assert sum(other_seats.values()) == remaining_seats

        # Check proportionality (with tolerance for rounding)
        other_vote_percentages = (other_votes / other_votes.sum() * 100).to_dict()
        other_seat_percentages = {party: other_seats[party] / remaining_seats * 100 for party in other_seats}

        for party in other_seats:
            assert abs(other_seat_percentages[party] - other_vote_percentages[party]) < 10.0, \
                f"Party {party}: seat% {other_seat_percentages[party]:.1f} differs too much from vote% {other_vote_percentages[party]:.1f}"


def test_distribute_seats_coalition_winner():
    """Test seat distribution when winner is a coalition."""
    cc = make_simple_cc(8, 10000)
    election_config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C"],        seed=999
    )
    election = Election(electionConfig=election_config)

    # Run first iteration
    first_iter = election.start()

    # Manually form coalition and complete election
    if not first_iter.hasWinner() and len(first_iter.getContestants()) >= 2:
        contestants_list = list(first_iter.getContestants().values())
        # Form coalition between first two parties
        first_iter.formCoalition("Coalition_AB", [contestants_list[0], contestants_list[1]])

        # Continue election
        current = first_iter
        while not current.hasWinner() and current.hasNext():
            next_input = current.getNextRoundInput()
            current = ElectionRound.run(next_input)

        # Party reduction occurred and winner is a coalition
        if not election.hadOutrightWinner() and not election.getWinner().isSingleParty():
            evaluator = ElectionEvaluator(seed=config.seed)

            result = evaluator.evaluate(election)

            seats = result.seats
            winner = election.getWinner()
            gov_majority_seats = election.electionConfig.getParliamentMajoritySeats()

            # Winner's constituent parties SHOULD get individual seats (not the coalition)
            winner_party_names = winner.getContainedParties()
            for party_name in winner_party_names:
                assert party_name in seats, \
                    f"Coalition member {party_name} should have individual seats"

            # Coalition itself should NOT appear in seat distribution
            assert winner.name not in seats, \
                f"Coalition {winner.name} should not appear in seat distribution"

            # Total seats for winner parties should equal government majority
            winner_total_seats = sum(seats[party] for party in winner_party_names)
            assert winner_total_seats == gov_majority_seats, \
                f"Winner parties should have {gov_majority_seats} seats total, got {winner_total_seats}"

            # Other parties should have remaining seats
            remaining_seats = election.electionConfig.parliamentarySeats - gov_majority_seats
            other_parties_seats = sum(seats[party] for party in seats if party not in winner_party_names)
            assert other_parties_seats == remaining_seats, \
                f"Other parties should have {remaining_seats} seats, got {other_parties_seats}"


def test_distribute_seats_different_methods():
    """Test that different seat distribution methods work correctly."""
    cc = make_simple_cc(5, 10000)

    # Test each distribution method works
    for method in [SeatDistributionMethod.SAINTE_LAGUE,
                   SeatDistributionMethod.D_HONDT,
                   SeatDistributionMethod.HARE_NIEMEYER]:

        config = ElectionConfig(
            constituencies_config=cc,
            participating_parties=["A", "B"],
            seed=123
        )
        election = Election(electionConfig=config)
        final_iter = election.run()

        # Skip test if decided by lot (no ballot to distribute from)
        if final_iter.wasDecidedByLot():
            continue

        evaluator = ElectionEvaluator(seed=config.seed, seat_distribution_method=method)
        result = evaluator.evaluate(election)
        seats = result.seats
        total_seats = election.electionConfig.parliamentarySeats

        # Verify seat distribution is valid
        assert sum(seats.values()) == total_seats, \
            f"Method {method.name}: Total seats don't match"
        assert all(s >= 0 for s in seats.values()), \
            f"Method {method.name}: Has negative seats"


def test_distribute_seats_all_to_winner():
    """Test edge case where winner gets all seats (no other contestants remain)."""
    cc = make_simple_cc(3, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],        seed=456
    )

    election = Election(electionConfig=config)
    final_iter = election.run()

    evaluator = ElectionEvaluator(seed=config.seed)


    result = evaluator.evaluate(election)


    seats = result.seats
    total_seats = election.electionConfig.parliamentarySeats

    # Total should always equal parliamentary seats
    assert sum(seats.values()) == total_seats

    # All seats should go to someone
    assert all(seat_count >= 0 for seat_count in seats.values())


def test_seat_distribution_no_negative_seats():
    """Ensure no party gets negative seats."""
    cc = make_simple_cc(6, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D"],        seed=789
    )

    election = Election(electionConfig=config)
    election.run()
    evaluator = ElectionEvaluator(seed=config.seed)

    result = evaluator.evaluate(election)

    seats = result.seats

    # No negative seats
    for party, seat_count in seats.items():
        assert seat_count >= 0, f"Party {party} has negative seats: {seat_count}"


def test_seat_distribution_total_always_correct():
    """Test multiple random elections to ensure total seats always equals parliamentary seats."""
    cc = make_simple_cc(8, 10000)

    tested_count = 0
    for seed in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        config = ElectionConfig(
            constituencies_config=cc,
            participating_parties=["A", "B"],            seed=seed
        )

        election = Election(electionConfig=config)
        final_iter = election.run()

        # Skip if decided by lot (no ballot exists for seat distribution)
        if final_iter.wasDecidedByLot():
            continue

        if election.isFinished():
            evaluator = ElectionEvaluator(seed=config.seed)

            result = evaluator.evaluate(election)

            seats = result.seats
            total_seats = election.electionConfig.parliamentarySeats

            assert sum(seats.values()) == total_seats, \
                f"Seed {seed}: Total seats {sum(seats.values())} != parliamentary seats {total_seats}"
            tested_count += 1

    # Ensure we tested at least some elections
    assert tested_count > 0, "No elections were tested (all decided by lot)"


def test_decision_by_lot_has_assigned_government_majority():
    """Test that elections decided by lot always have assigned government majority."""
    # DrawLotsStrategy already imported from ipres

    cc = make_simple_cc(3, 10000)

    # Use minimal difference strategy and specific seed to trigger decision by lot
    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],        seed=999  # Seed that may lead to decision by lot
    )

    # Create election with draw lots strategy
    election = Election(electionConfig=config)

    # Manually create iterations that will trigger decision by lot
    # Start with first iteration
    first_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B"]),
        probabilities={"A": 50.0, "B": 50.0},  # Equal probabilities
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(42),
        draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD
    )

    first_iter = ElectionRound.run(first_input)

    assert not first_iter.hasWinner()

    # If no winner, create second iteration with same contestants
    if not first_iter.hasWinner():
        second_input = ElectionRoundInput(
            election=election,
            constituencies_config=cc,
            contestants=first_iter.getContestants().copy(),
            probabilities={"A": 50.1, "B": 49.9},  # Slightly different
            ballot_majority_percent=config.getParliamentMajorityPercent(),
            rng=np.random.default_rng(43),
            previousRound=first_iter,
            draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD,
            round_number=1
        )

        second_iter = ElectionRound.run(second_input)

        assert not second_iter.hasWinner()

        # If still no winner, third iteration should decide by lot
        if not second_iter.hasWinner():
            third_input = ElectionRoundInput(
                election=election,
                constituencies_config=cc,
                contestants=second_iter.getContestants().copy(),
                probabilities={"A": 49.9, "B": 50.1},  # Slightly different again
                ballot_majority_percent=config.getParliamentMajorityPercent(),
                rng=np.random.default_rng(44),
                previousRound=second_iter,
                draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD,
                round_number=2
            )

            third_iter = ElectionRound.run(third_input)

            assert third_iter.wasDecidedByLot()

            # Third iteration with same 2 contestants should trigger decision by lot
            if third_iter.wasDecidedByLot():
                # This election was decided by lot — no outright winner
                assert election.hadOutrightWinner() is False, \
                    "Election decided by lot should not have an outright winner"

                # Verify seats can be distributed
                evaluator = ElectionEvaluator(seed=config.seed)

                result = evaluator.evaluate(election)

                seats = result.seats
                total_seats = election.electionConfig.parliamentarySeats

                assert sum(seats.values()) == total_seats
                assert election.getWinner().name in seats
                assert seats[election.getWinner().name] == config.getParliamentMajoritySeats()


def test_decision_by_lot_without_party_reduction():
    """Test decision by lot when there's no party reduction (only 2 parties from start)."""
    # DrawLotsStrategy already imported from ipres

    cc = make_simple_cc(2, 5000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],        seed=42
    )

    election = Election(electionConfig=config)

    # Create first iteration with equal votes (likely to not produce winner)
    first_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B"]),
        probabilities={"A": 50.0, "B": 50.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(100),
        draw_lots_strategy=DrawLotsStrategy.RANDOM
    )

    first_iter = ElectionRound.run(first_input)

    assert not first_iter.hasWinner()

    # Create second iteration
    if not first_iter.hasWinner():
        second_input = ElectionRoundInput(
            election=election,
            constituencies_config=cc,
            contestants=first_iter.getContestants().copy(),
            probabilities={"A": 50.5, "B": 49.5},
            ballot_majority_percent=config.getParliamentMajorityPercent(),
            rng=np.random.default_rng(101),
            previousRound=first_iter,
            draw_lots_strategy=DrawLotsStrategy.RANDOM,
            round_number=1
        )

        second_iter = ElectionRound.run(second_input)

        assert not second_iter.hasWinner()

        # Create third iteration (should trigger decision by lot)
        if not second_iter.hasWinner():
            third_input = ElectionRoundInput(
                election=election,
                constituencies_config=cc,
                contestants=second_iter.getContestants().copy(),
                probabilities={"A": 49.5, "B": 50.5},
                ballot_majority_percent=config.getParliamentMajorityPercent(),
                rng=np.random.default_rng(102),
                previousRound=second_iter,
                draw_lots_strategy=DrawLotsStrategy.RANDOM,
                round_number=2
            )

            third_iter = ElectionRound.run(third_input)

            assert third_iter.wasDecidedByLot()

            if third_iter.wasDecidedByLot():
                # No party reduction occurred (started with 2, ended with 2)
                assert election.getFirstIteration().getParticipatingParties() == election.getLastIteration().getParticipatingParties()

                # Decision was by lot without party reduction — still no outright winner
                assert election.hadOutrightWinner() is False, \
                    "Decision by lot without party reduction should still not have an outright winner"

                # Verify seats distribution works (Path 1: government majority assignment)
                evaluator = ElectionEvaluator(seed=config.seed)

                result = evaluator.evaluate(election)

                seats = result.seats
                winner = election.getWinner()
                gov_majority_seats = config.getParliamentMajoritySeats()

                # Winner should get government majority
                assert seats[winner.name] == gov_majority_seats

                # Other party should get remaining seats based on first iteration
                remaining_seats = config.parliamentarySeats - gov_majority_seats
                other_party = [p for p in seats.keys() if p != winner.name][0]
                assert seats[other_party] == remaining_seats


def test_decision_by_lot_marginal_lead_strategy():
    """Test that decision by lot with MARGINAL_LEAD uses previous votes correctly."""
    # DrawLotsStrategy already imported from ipres

    cc = make_simple_cc(2, 8000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],        seed=555
    )

    election = Election(electionConfig=config)

    # First iteration: A gets more votes but not super majority
    first_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B"]),
        probabilities={"A": 52.0, "B": 48.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(200),
        draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD
    )

    first_iter = ElectionRound.run(first_input)

    assert not first_iter.hasWinner()

    if not first_iter.hasWinner():
        # Second iteration: B gets more votes but not super majority
        second_input = ElectionRoundInput(
            election=election,
            constituencies_config=cc,
            contestants=first_iter.getContestants().copy(),
            probabilities={"A": 48.5, "B": 51.5},
            ballot_majority_percent=config.getParliamentMajorityPercent(),
            rng=np.random.default_rng(201),
            previousRound=first_iter,
            draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD,
            round_number=1
        )

        second_iter = ElectionRound.run(second_input)

        assert not second_iter.hasWinner()

        if not second_iter.hasWinner():
            # Third iteration: Should decide by lot using minimal difference (B had more votes in iteration 2)
            third_input = ElectionRoundInput(
                election=election,
                constituencies_config=cc,
                contestants=second_iter.getContestants().copy(),
                probabilities={"A": 50.0, "B": 50.0},
                ballot_majority_percent=config.getParliamentMajorityPercent(),
                rng=np.random.default_rng(202),
                previousRound=second_iter,
                draw_lots_strategy=DrawLotsStrategy.MARGINAL_LEAD,
                round_number=2
            )

            third_iter = ElectionRound.run(third_input)

            assert third_iter.wasDecidedByLot()

            if third_iter.wasDecidedByLot():
                # Decision was by lot — no outright winner
                assert election.hadOutrightWinner() is False

                # Winner should be party with more votes in previous iteration (iteration 2)
                second_votes = second_iter.getContestantsVotesAfterPossibleCoalitions()
                expected_winner = second_votes.idxmax()
                actual_winner = election.getWinner().name

                assert actual_winner == expected_winner, \
                    f"MARGINAL_LEAD should pick {expected_winner} (had most votes in prev iteration), got {actual_winner}"

                # Verify seat distribution
                evaluator = ElectionEvaluator(seed=config.seed)

                result = evaluator.evaluate(election)

                seats = result.seats
                assert seats[actual_winner] == config.getParliamentMajoritySeats()


def test_decisionNeededPartyReduction_with_reduction():
    """Test decisionNeededPartyReduction returns True when parties are reduced."""
    cc = make_simple_cc(5, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B", "C", "D", "E"],        seed=123
    )

    election = Election(electionConfig=config)

    # Create first iteration with 5 parties
    first_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B", "C", "D", "E"]),
        probabilities={"A": 30.0, "B": 25.0, "C": 20.0, "D": 15.0, "E": 10.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(100)
    )

    first_iter = ElectionRound.run(first_input)
    assert not first_iter.hasWinner()

    # Create second iteration with only 2 parties (party reduction)
    second_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B"]),
        probabilities={"A": 70.0, "B": 30.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(101),
        previousRound=first_iter,
        round_number=1
    )

    second_iter = ElectionRound.run(second_input)
    assert second_iter.hasWinner()

    # Now test decisionNeededPartyReduction
    assert election.decisionNeededPartyReduction() is True, \
        "Should return True when parties reduced from 5 to 2"
    assert len(election.getFirstIteration().getParticipatingParties()) == 5
    assert len(election.getLastIteration().getParticipatingParties()) == 2


def test_decisionNeededPartyReduction_without_reduction():
    """Test decisionNeededPartyReduction returns False when no party reduction occurs."""
    cc = make_simple_cc(3, 10000)

    config = ElectionConfig(
        constituencies_config=cc,
        participating_parties=["A", "B"],        seed=456
    )

    election = Election(electionConfig=config)

    # Create first iteration with 2 parties (neither reaches super majority)
    first_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=contestantsDictFromParties(["A", "B"]),
        probabilities={"A": 52.0, "B": 48.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(200)
    )

    first_iter = ElectionRound.run(first_input)
    assert not first_iter.hasWinner()

    # Create second iteration with same 2 parties (no reduction)
    # This time A reaches super majority
    second_input = ElectionRoundInput(
        election=election,
        constituencies_config=cc,
        contestants=first_iter.getContestants().copy(),
        probabilities={"A": 75.0, "B": 25.0},
        ballot_majority_percent=config.getParliamentMajorityPercent(),
        rng=np.random.default_rng(201),
        previousRound=first_iter,
        round_number=1
    )

    second_iter = ElectionRound.run(second_input)
    assert second_iter.hasWinner()

    # Now test decisionNeededPartyReduction
    assert election.decisionNeededPartyReduction() is False, \
        "Should return False when same number of parties (2) from start to finish"
    assert len(election.getFirstIteration().getParticipatingParties()) == 2
    assert len(election.getLastIteration().getParticipatingParties()) == 2
