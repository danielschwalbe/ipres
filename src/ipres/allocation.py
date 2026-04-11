"""
Constituency allocation strategies for distributing constituencies to parties.

This module provides different strategies for assigning constituencies to parties
based on importance metrics, quotas, and other criteria.
"""
from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment

class ConstituencyAllocationMethod(Enum):
    GREEDY = "greedy"
    STABLE_MATCHING = "stable_matching"
    OPTIMAL = "optimal"

class ConstituencyAllocationStrategy(ABC):
    """Base class for constituency allocation strategies."""

    @abstractmethod
    def allocate(self,
                 importance_matrix: pd.DataFrame,
                 quotas: Dict[str, int],
                 rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
        """
        Allocate constituencies to parties based on importance and quotas.

        Args:
            importance_matrix: DataFrame with constituencies as rows and parties as columns.
                             Each element w_ij represents the importance of constituency i for party j.
            quotas: Dictionary mapping party names to the number of constituencies they should receive.
                   Sum of quotas must equal number of constituencies.
            rng: Random number generator for tie-breaking (optional).

        Returns:
            Dictionary mapping constituency names to party names.

        Raises:
            ValueError: If sum of quotas doesn't match number of constituencies.
        """
        pass


class GreedyAllocationStrategy(ConstituencyAllocationStrategy):
    """
    Greedy allocation strategy: repeatedly assign the (constituency, party) pair
    with the highest importance, respecting quotas.

    This is a simple, intuitive strategy that prioritizes parties' most important
    constituencies first.
    """

    def allocate(self,
                 importance_matrix: pd.DataFrame,
                 quotas: Dict[str, int],
                 rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
        """
        Allocate constituencies using greedy strategy.

        The algorithm:
        1. Find the (constituency, party) pair with highest importance
        2. If party hasn't reached quota, assign constituency to party
        3. Remove constituency from consideration
        4. Repeat until all constituencies assigned

        Args:
            importance_matrix: Importance of each constituency for each party
            quotas: Number of constituencies each party should receive
            rng: Random generator for tie-breaking

        Returns:
            Dictionary mapping constituency name -> party name
        """
        if rng is None:
            rng = np.random.default_rng()

        # Validate quotas
        total_quotas = sum(quotas.values())
        n_constituencies = len(importance_matrix)
        if total_quotas != n_constituencies:
            raise ValueError(
                f"Sum of quotas ({total_quotas}) must equal number of constituencies ({n_constituencies})"
            )

        # Initialize tracking
        allocation = {}  # constituency -> party
        remaining_quotas = quotas.copy()
        available_constituencies = set(importance_matrix.index)

        # Create a list of (importance, constituency, party) tuples for sorting
        candidates = []
        for constituency in importance_matrix.index:
            for party in importance_matrix.columns:
                importance = importance_matrix.loc[constituency, party]
                candidates.append((importance, constituency, party))

        # Sort by importance (descending), add random tie-breaker
        candidates.sort(key=lambda x: (x[0], rng.random()), reverse=True)

        # Greedy assignment
        for importance, constituency, party in candidates:
            # Skip if constituency already assigned
            if constituency not in available_constituencies:
                continue

            # Skip if party has reached quota
            if remaining_quotas.get(party, 0) <= 0:
                continue

            # Assign constituency to party
            allocation[constituency] = party
            remaining_quotas[party] -= 1
            available_constituencies.remove(constituency)

            # Early exit if all constituencies assigned
            if not available_constituencies:
                break

        return allocation


class StableMatchingAllocationStrategy(ConstituencyAllocationStrategy):
    """
    Stable matching allocation strategy based on Gale-Shapley algorithm.

    Creates a stable allocation where no constituency-party pair would both
    prefer each other over their current assignments.

    This is a modified version for the many-to-one matching problem where
    each party can be assigned multiple constituencies (up to their quota).
    """

    def allocate(self,
                 importance_matrix: pd.DataFrame,
                 quotas: Dict[str, int],
                 rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
        """
        Allocate constituencies using stable matching strategy.

        Uses a modified Gale-Shapley algorithm where:
        - Constituencies "propose" to parties in order of importance (from party's perspective)
        - Parties accept/reject based on their current assignments and quotas
        - Results in a stable matching

        Args:
            importance_matrix: Importance of each constituency for each party
            quotas: Number of constituencies each party should receive
            rng: Random generator for tie-breaking

        Returns:
            Dictionary mapping constituency name -> party name
        """
        if rng is None:
            rng = np.random.default_rng()

        # Validate quotas
        total_quotas = sum(quotas.values())
        n_constituencies = len(importance_matrix)
        if total_quotas != n_constituencies:
            raise ValueError(
                f"Sum of quotas ({total_quotas}) must equal number of constituencies ({n_constituencies})"
            )

        # Create preference lists
        # For each constituency: which parties value it most (from party's perspective)
        constituency_prefs = {}
        for constituency in importance_matrix.index:
            # Sort parties by how much they value this constituency
            party_importances = importance_matrix.loc[constituency].copy()
            # Add small random noise for tie-breaking
            party_importances += rng.uniform(0, 1e-10, len(party_importances))
            sorted_parties = party_importances.sort_values(ascending=False).index.tolist()
            constituency_prefs[constituency] = sorted_parties

        # For each party: rank constituencies by importance
        party_prefs = {}
        for party in importance_matrix.columns:
            constituency_importances = importance_matrix[party].copy()
            # Add small random noise for tie-breaking
            constituency_importances += rng.uniform(0, 1e-10, len(constituency_importances))
            sorted_constituencies = constituency_importances.sort_values(ascending=False).index.tolist()
            party_prefs[party] = sorted_constituencies

        # Run modified Gale-Shapley algorithm
        allocation = {}  # constituency -> party
        party_assignments = {party: [] for party in quotas.keys()}  # party -> [constituencies]
        free_constituencies = list(importance_matrix.index)
        next_proposal_index = {c: 0 for c in importance_matrix.index}  # Track proposals

        while free_constituencies:
            # Pick a free constituency
            constituency = free_constituencies[0]

            # Get next party on this constituency's preference list
            proposal_idx = next_proposal_index[constituency]

            # Check if constituency has exhausted all options
            if proposal_idx >= len(constituency_prefs[constituency]):
                # This shouldn't happen if quotas sum correctly
                raise ValueError(f"Constituency {constituency} has no proposals left.")
                #free_constituencies.remove(constituency)
                #continue

            party = constituency_prefs[constituency][proposal_idx]
            next_proposal_index[constituency] += 1

            # Check if party has quota and would accept this constituency
            current_assignments = party_assignments[party]
            quota = quotas[party]

            if len(current_assignments) < quota:
                # Party has space, accept the constituency
                allocation[constituency] = party
                party_assignments[party].append(constituency)
                free_constituencies.remove(constituency)

            else:
                # Party is full, check if this constituency is better than worst current assignment
                party_pref_list = party_prefs[party]

                # Find the least preferred constituency currently assigned to this party
                worst_current = None
                worst_rank = -1
                for assigned_constituency in current_assignments:
                    rank = party_pref_list.index(assigned_constituency)
                    if rank > worst_rank:
                        worst_rank = rank
                        worst_current = assigned_constituency

                # Check if proposing constituency is preferred over worst current
                proposing_rank = party_pref_list.index(constituency)
                if proposing_rank < worst_rank:
                    # Replace worst current with proposing constituency
                    allocation[constituency] = party
                    party_assignments[party].remove(worst_current)
                    party_assignments[party].append(constituency)
                    del allocation[worst_current]

                    # Worst constituency becomes free again
                    free_constituencies.remove(constituency)
                    free_constituencies.append(worst_current)

        return allocation


# Convenience functions for direct use
def allocate_constituencies_greedy(importance_matrix: pd.DataFrame,
                                   quotas: Dict[str, int],
                                   rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
    """
    Convenience function to allocate constituencies using greedy strategy.

    Args:
        importance_matrix: Importance of each constituency for each party
        quotas: Number of constituencies each party should receive
        rng: Random generator for tie-breaking

    Returns:
        Dictionary mapping constituency name -> party name
    """
    strategy = GreedyAllocationStrategy()
    return strategy.allocate(importance_matrix, quotas, rng)


def allocate_constituencies_stable(importance_matrix: pd.DataFrame,
                                   quotas: Dict[str, int],
                                   rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
    """
    Convenience function to allocate constituencies using stable matching strategy.

    Args:
        importance_matrix: Importance of each constituency for each party
        quotas: Number of constituencies each party should receive
        rng: Random generator for tie-breaking

    Returns:
        Dictionary mapping constituency name -> party name
    """
    strategy = StableMatchingAllocationStrategy()
    return strategy.allocate(importance_matrix, quotas, rng)


class OptimalAllocationStrategy(ConstituencyAllocationStrategy):
    """
    Optimal allocation strategy using Linear Programming / Hungarian Algorithm.

    Finds the allocation that **provably** maximizes the total importance score.
    Uses scipy's implementation of the Hungarian algorithm (Kuhn-Munkres).

    This is more computationally expensive than Greedy but guarantees optimality.
    """

    def allocate(self,
                 importance_matrix: pd.DataFrame,
                 quotas: Dict[str, int],
                 rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
        """
        Allocate constituencies using optimal matching (Hungarian algorithm).

        This solves the assignment problem optimally by:
        1. Creating "slots" for each party based on their quota
        2. Using Hungarian algorithm to find maximum weighted matching
        3. Mapping back to party assignments

        Args:
            importance_matrix: Importance of each constituency for each party
            quotas: Number of constituencies each party should receive
            rng: Random generator (not used, included for API consistency)

        Returns:
            Dictionary mapping constituency name -> party name

        Raises:
            ValueError: If sum of quotas doesn't match number of constituencies
        """
        # Validate quotas
        total_quotas = sum(quotas.values())
        n_constituencies = len(importance_matrix)
        if total_quotas != n_constituencies:
            raise ValueError(
                f"Sum of quotas ({total_quotas}) must equal number of constituencies ({n_constituencies})"
            )

        # Create expanded cost matrix:
        # Rows = constituencies
        # Columns = "slots" (each party gets quota number of slots)
        constituencies = list(importance_matrix.index)
        parties = list(importance_matrix.columns)

        # Build slot mapping: slot_index -> party_name
        slot_to_party = []
        for party in parties:
            slot_to_party.extend([party] * quotas[party])

        n_slots = len(slot_to_party)

        # Build cost matrix
        # cost_matrix[i][j] = importance of constituency i for party of slot j
        cost_matrix = np.zeros((n_constituencies, n_slots))

        for i, constituency in enumerate(constituencies):
            for j, party in enumerate(slot_to_party):
                cost_matrix[i, j] = importance_matrix.loc[constituency, party]

        # Solve using Hungarian algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix, maximize=True)

        # Build allocation dictionary
        allocation = {}
        for const_idx, slot_idx in zip(row_ind, col_ind):
            constituency = constituencies[const_idx]
            party = slot_to_party[slot_idx]
            allocation[constituency] = party

        return allocation


def allocate_constituencies_optimal(importance_matrix: pd.DataFrame,
                                    quotas: Dict[str, int],
                                    rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
    """
    Convenience function to allocate constituencies using optimal strategy.

    This finds the provably optimal allocation that maximizes total importance.
    Uses the Hungarian algorithm (more expensive than Greedy but guaranteed optimal).

    Args:
        importance_matrix: Importance of each constituency for each party
        quotas: Number of constituencies each party should receive
        rng: Random generator (not used, included for API consistency)

    Returns:
        Dictionary mapping constituency name -> party name
    """
    strategy = OptimalAllocationStrategy()
    return strategy.allocate(importance_matrix, quotas, rng)

def create_constituency_allocation_strategy(method: ConstituencyAllocationMethod) -> ConstituencyAllocationStrategy:
    """Creates a constituency allocation strategy based on the given method."""
    match method:
        case ConstituencyAllocationMethod.GREEDY:
            return GreedyAllocationStrategy()
        case ConstituencyAllocationMethod.STABLE_MATCHING:
            return StableMatchingAllocationStrategy()
        case ConstituencyAllocationMethod.OPTIMAL:
            return OptimalAllocationStrategy()
        case _:
            raise ValueError(f"Invalid allocation method: {method}")

def allocate_constituencies(importance_matrix: pd.DataFrame,
                            quotas: Dict[str, int],
                            allocation_method: ConstituencyAllocationMethod,
                            rng: Optional[np.random.Generator] = None) -> Dict[str, str]:
    """Allocates constituencies based on the given importance matrix and quotas using the specified allocation method."""
    strategy = create_constituency_allocation_strategy(allocation_method)
    return strategy.allocate(importance_matrix, quotas, rng)