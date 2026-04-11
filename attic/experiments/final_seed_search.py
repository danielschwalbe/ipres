#!/usr/bin/env python3
"""Final search for Union win seeds."""

import sys
sys.path.insert(0, '../../src')
import warnings
warnings.filterwarnings('ignore')

import numpy as np
from ipres import contestantsFromParties, Election, ElectionConfig, ConstituenciesConfig, VoteMatrix, SuperMajorityMargin, MarginUnit
from ipres.bundestagswahl_loader import load_bundestagswahl_data
from ipres import ElectionRoundInput as IterationInput

# Load data
constituencies_df, vote_matrix, party_names = load_bundestagswahl_data(2021)
constituencies_config = ConstituenciesConfig(constituencies=constituencies_df)
contestants = contestantsFromParties(party_names)
vote_matrix_real = VoteMatrix.generate(constituencies_config, contestants, vote_matrix=vote_matrix)

def run_election(_seed):
    config = ElectionConfig(constituencies_config=constituencies_config,
                            participating_parties=party_names, seed=_seed,
                            parliament_majority_margin=SuperMajorityMargin(10, MarginUnit.SEATS))
    election = Election(electionConfig=config)
    inp = IterationInput(election, constituencies_config,
                         {c.name: c for c in contestants},
                         ballot_majority_percent=config.getParliamentMajorityPercent(),
                         rng = np.random.default_rng(_seed), vote_matrix=vote_matrix_real)
    it = election.start(inp)
    it.formCoalition('Union', ['CDU', 'CSU'])

    for _ in range(20):
        if not it.hasNext(): break
        it = election.runNextIteration()

    if election.hasWinner():
        return election.getWinner().name, election.getLastIteration().wasDecidedByLot()
    return None, None

# Test known good seeds first
print("Teste bekannte Seeds...")
for s in [151, 100, 200, 42, 1000]:
    w, lot = run_election(s)
    if w == 'Union':
        typ = 'LOSENTSCHEID' if lot else 'DIREKT'
        print(f"  Seed {s}: Union gewinnt durch {typ}")
    else:
        print(f"  Seed {s}: {w} gewinnt")

# Quick search
print("\nSuche nach weiteren Union-Siegen (0-10000)...")
union_direct = union_lot = None
for seed in range(10000):
    if seed % 1000 == 0:
        print(f"  Seed {seed}...", end='\r')
    w, lot = run_election(seed)
    if w == 'Union':
        if not lot and not union_direct:
            union_direct = seed
            print(f"\n  ✓ Union DIREKT: Seed {seed}")
        if lot and not union_lot:
            union_lot = seed
    if union_direct and union_lot:
        break

print(f"\n\n{'='*60}")
print("ERGEBNIS:")
print(f"  Union gewinnt DIREKT bei Seed: {union_direct}")
print(f"  Union gewinnt durch LOSENTSCHEID bei Seed: {union_lot if union_lot else 151}")
