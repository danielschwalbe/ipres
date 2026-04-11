"""
Manually crafted example where Greedy and Stable Matching differ.
"""

import numpy as np
import pandas as pd
from ipres.allocation import allocate_constituencies_greedy, allocate_constituencies_stable


def print_allocation_details(importance_matrix, allocation, strategy_name):
    """Print detailed allocation information."""
    print(f"\n{'='*70}")
    print(f"{strategy_name} Allocation:")
    print(f"{'='*70}")

    # Group by party
    party_assignments = {}
    for constituency, party in allocation.items():
        if party not in party_assignments:
            party_assignments[party] = []
        party_assignments[party].append(constituency)

    # Calculate totals
    for party in sorted(party_assignments.keys()):
        constituencies = sorted(party_assignments[party])
        total_importance = sum(importance_matrix.loc[c, party] for c in constituencies)

        print(f"\n{party} bekommt: {', '.join(constituencies)}")
        print(f"  Details:")
        for c in constituencies:
            imp = importance_matrix.loc[c, party]
            print(f"    {c}: {imp:.4f}")
        print(f"  Summe: {total_importance:.4f}")

    # Calculate global total
    global_total = 0
    for constituency, party in allocation.items():
        global_total += importance_matrix.loc[constituency, party]

    print(f"\n{'─'*70}")
    print(f"Gesamt-Wichtigkeit (alle Parteien): {global_total:.4f}")
    print(f"{'─'*70}")


def main():
    print("Konstruiertes Beispiel für unterschiedliche Ergebnisse\n")

    # Create a carefully crafted scenario
    # The key: Create a situation where Greedy takes the highest value first,
    # but this blocks a better overall stable matching

    importance_matrix = pd.DataFrame({
        "Partei_A": [0.60, 0.55, 0.20, 0.15],  # A really wants WK1 and WK2
        "Partei_B": [0.58, 0.30, 0.57, 0.56]   # B also wants WK1, but really needs WK3, WK4
    }, index=["WK1", "WK2", "WK3", "WK4"])

    quotas = {"Partei_A": 2, "Partei_B": 2}

    print("="*70)
    print("Importance Matrix:")
    print("="*70)
    print(importance_matrix)
    print()
    print(f"Quotas: {quotas}")
    print()

    print("Analyse der Importance-Werte:")
    print("-" * 70)
    print("WK1: Partei_A (0.60) vs Partei_B (0.58) - Knapp! A gewinnt")
    print("WK2: Partei_A (0.55) >> Partei_B (0.30) - Klar A")
    print("WK3: Partei_B (0.57) >> Partei_A (0.20) - Klar B")
    print("WK4: Partei_B (0.56) >> Partei_A (0.15) - Klar B")

    # Run Greedy
    print("\n" + "="*70)
    print("GREEDY-ALGORITHMUS (Schritt für Schritt):")
    print("="*70)
    print("\nSortiere alle (Wahlkreis, Partei) Paare nach Wichtigkeit:")
    print("1. WK1 → Partei_A (0.60)")
    print("2. WK1 → Partei_B (0.58)")
    print("3. WK3 → Partei_B (0.57)")
    print("4. WK4 → Partei_B (0.56)")
    print("5. WK2 → Partei_A (0.55)")
    print("6. WK2 → Partei_B (0.30)")
    print("7. WK3 → Partei_A (0.20)")
    print("8. WK4 → Partei_A (0.15)")

    print("\nZuweisungs-Prozess:")
    print("  1. WK1 → Partei_A (0.60) ✓")
    print("  2. WK1 → Partei_B (0.58) ✗ (WK1 schon vergeben)")
    print("  3. WK3 → Partei_B (0.57) ✓")
    print("  4. WK4 → Partei_B (0.56) ✓ (Partei_B Quote voll)")
    print("  5. WK2 → Partei_A (0.55) ✓ (Partei_A Quote voll)")

    greedy_alloc = allocate_constituencies_greedy(
        importance_matrix, quotas, np.random.default_rng(42)
    )

    print_allocation_details(importance_matrix, greedy_alloc, "GREEDY")

    # Check for blocking pairs
    print("\n" + "="*70)
    print("PRÜFUNG AUF BLOCKING PAIRS in Greedy:")
    print("="*70)

    # Manual check for WK1 and Partei_B
    print("\nKann (WK1, Partei_B) ein blocking pair sein?")
    print("  - WK1 ist aktuell bei Partei_A mit Wichtigkeit 0.60")
    print("  - Partei_B schätzt WK1 mit 0.58")
    print("  - Würde Partei_B einen ihrer Wahlkreise für WK1 aufgeben?")
    print("    • Aktuell hat B: WK3 (0.57), WK4 (0.56)")
    print("    • WK1 für B hat Wichtigkeit 0.58")
    print("    • 0.58 > 0.56 (WK4) → JA! B würde WK4 gegen WK1 tauschen")
    print("  - Würde WK1 lieber zu B (0.58) als bei A (0.60) bleiben?")
    print("    • NEIN! 0.60 > 0.58 → WK1 bevorzugt A")
    print("\n  → KEIN blocking pair, weil WK1 A bevorzugt")

    # Now let's try a different matrix where blocking pairs exist
    print("\n\n" + "#"*70)
    print("# NEUES BEISPIEL mit echtem Blocking Pair")
    print("#"*70 + "\n")

    # This time, make it so Greedy creates an unstable situation
    importance_matrix2 = pd.DataFrame({
        "Partei_A": [0.51, 0.50, 0.30, 0.29],  # A slightly prefers WK1, WK2
        "Partei_B": [0.49, 0.40, 0.70, 0.69]   # B strongly prefers WK3, WK4 but also likes WK1
    }, index=["WK1", "WK2", "WK3", "WK4"])

    print("="*70)
    print("Neue Importance Matrix:")
    print("="*70)
    print(importance_matrix2)
    print()

    print("Analyse:")
    print("-" * 70)
    print("WK1: Partei_A (0.51) vs Partei_B (0.49) - Knapp! A gewinnt")
    print("WK2: Partei_A (0.50) > Partei_B (0.40)")
    print("WK3: Partei_B (0.70) >> Partei_A (0.30) - B braucht WK3!")
    print("WK4: Partei_B (0.69) >> Partei_A (0.29) - B braucht WK4!")

    greedy_alloc2 = allocate_constituencies_greedy(
        importance_matrix2, quotas, np.random.default_rng(42)
    )

    print_allocation_details(importance_matrix2, greedy_alloc2, "GREEDY")

    # Run Stable Matching
    print("\n" + "="*70)
    print("STABLE MATCHING-ALGORITHMUS:")
    print("="*70)

    print("\nWahlkreise 'bewerben' sich bei Parteien (basierend auf Parteipräferenzen):")
    print("\nPräferenz-Listen der Parteien:")
    print("  Partei_A ranked: WK1 (0.51) > WK2 (0.50) > WK3 (0.30) > WK4 (0.29)")
    print("  Partei_B ranked: WK3 (0.70) > WK4 (0.69) > WK1 (0.49) > WK2 (0.40)")

    print("\nWahlkreise bewerben sich (bevorzugen die Partei, die sie höher schätzt):")
    print("  WK1: bevorzugt A (0.51 > 0.49)")
    print("  WK2: bevorzugt A (0.50 > 0.40)")
    print("  WK3: bevorzugt B (0.70 > 0.30)")
    print("  WK4: bevorzugt B (0.69 > 0.29)")

    stable_alloc2 = allocate_constituencies_stable(
        importance_matrix2, quotas, np.random.default_rng(42)
    )

    print_allocation_details(importance_matrix2, stable_alloc2, "STABLE MATCHING")

    # Compare
    if greedy_alloc2 == stable_alloc2:
        print("\n⚠️  Beide Strategien führen zum selben Ergebnis!")
    else:
        print("\n✓ Die Strategien führen zu UNTERSCHIEDLICHEN Ergebnissen!")

        print("\n" + "="*70)
        print("UNTERSCHIEDE:")
        print("="*70)
        for constituency in importance_matrix2.index:
            if greedy_alloc2[constituency] != stable_alloc2[constituency]:
                greedy_party = greedy_alloc2[constituency]
                stable_party = stable_alloc2[constituency]
                greedy_imp = importance_matrix2.loc[constituency, greedy_party]
                stable_imp = importance_matrix2.loc[constituency, stable_party]

                print(f"\n{constituency}:")
                print(f"  Greedy:  → {greedy_party} (Wichtigkeit: {greedy_imp:.4f})")
                print(f"  Stable:  → {stable_party} (Wichtigkeit: {stable_imp:.4f})")


if __name__ == "__main__":
    main()
