# Zuweisung von Wahlkreisen zu Parteien

Im letzten Schritt der Auswertung wird jedem Wahlkreis genau eine Partei zur Vertretung zugewiesen. Die Grundidee: Ein Wahlkreis soll möglichst von der Partei vertreten werden, für die er relativ zu ihren anderen Wahlkreisen am wichtigsten ist.

---

## Relative Wichtigkeit

Zunächst wird für jede Kombination aus Wahlkreis und Partei eine **Wichtigkeit** berechnet. Sie gibt an, wie stark ein Wahlkreis im Vergleich zu den übrigen Wahlkreisen zum Stimmenanteil der Partei beiträgt.

Sei `r_ij` der Stimmanteil von Partei `j` in Wahlkreis `i` (bezogen auf alle Stimmen in diesem Wahlkreis). Dann gilt:

```
w_ij = (M − 1) · r_ij / Σ(r_kj  für alle k ≠ i)
```

Die Normierung auf `(M−1)` stellt sicher, dass bei gleichmäßiger Stimmenverteilung überall `w = 1,0` gilt:

- `w > 1,0` → Wahlkreis ist für diese Partei überdurchschnittlich wichtig
- `w < 1,0` → unterdurchschnittlich wichtig
- `w = 1,0` → Durchschnitt

**Beispiel** (5 Wahlkreise, Parteien A / B / C):

| Wahlkreis | A    | B    | C    |
|-----------|------|------|------|
| WK1       | 1.22 | 0.70 | 0.73 |
| WK2       | 0.80 | 1.40 | 1.20 |
| WK3       | 0.90 | 0.91 | 1.78 |
| WK4       | 1.11 | 0.91 | 0.73 |
| WK5       | 1.00 | 1.14 | 0.73 |

A ist in WK1 am stärksten, B in WK2, C in WK3. Das Ergebnis der Zuteilung (A: 3 Wahlkreise, B: 2, C: 0) ist `{WK1: A, WK2: B, WK3: A, WK4: A, WK5: B}`.

---

## Zuteilungsmethoden

Aus der Wichtigkeitsmatrix und den Wahlkreisanzahlen pro Partei wird eine Zuteilung berechnet. Drei Methoden stehen zur Auswahl:

| Methode | Beschreibung |
|---|---|
| `OPTIMAL` *(Standard)* | Ungarischer Algorithmus (Kuhn-Munkres). Findet die Zuteilung mit dem global maximalen Gesamtwichtigkeitswert. Rechenaufwändiger, aber optimal. |
| `GREEDY` | Weist iterativ jeweils das (Wahlkreis, Partei)-Paar mit dem höchsten Wichtigkeitswert zu, solange das Kontingent der Partei noch nicht erschöpft ist. Schnell, aber nicht global optimal. |
| `STABLE_MATCHING` | Gale-Shapley-Algorithmus (stabile Zuordnung). Kein Wahlkreis-Partei-Paar würde gleichzeitig eine andere Zuordnung bevorzugen. |

---

## Einfluss von `constituency_representation`

- **`ENTIRE_PARLIAMENT`** *(Standard)*: Die Wichtigkeit wird aus den Stimmen aller Parteien berechnet.
- **`GOVERNING_MAJORITY`**: Nur die Stimmen der Regierungsparteien fließen in die Wichtigkeitsberechnung ein.

---

## Konfigurationsparameter

| Parameter | Klasse | Beschreibung |
|---|---|---|
| `constituency_allocation_method` | `ElectionEvaluator` | Zuteilungsmethode (Standard: `OPTIMAL`) |
| `constituency_representation` | `ElectionConfig` + `ElectionEvaluator` | Basis für die Wichtigkeitsberechnung |

---

## Ausführung in der Simulation

Die Klasse [`ConstituencyAssigner`](../../src/ipres/constituency_assigner.py) führt diesen Schritt durch. Sie nimmt das Ergebnis der Wahlkreisanzahlzuordnung als Eingabe entgegen.

```python
from ipres import (Election, ElectionConfig, ConstituenciesConfig,
                   SeatDistributor, ConstituencyCountDeterminer, ConstituencyAssigner,
                   SuperMajorityMargin, MarginUnit)
import pandas as pd

cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
    'constituency_name': ['WK1', 'WK2', 'WK3', 'WK4', 'WK5'],
    'constituency_size': [100_000] * 5,
}))
config = ElectionConfig(
    constituencies_config=cc,
    participating_parties=['A', 'B', 'C'],
    parliament_majority_margin=SuperMajorityMargin(5.0, MarginUnit.PERCENT),
    seed=42,
)

election = Election(electionConfig=config)
votes = {
    'WK1': {'A': 70, 'B': 20, 'C': 10},
    'WK2': {'A': 50, 'B': 35, 'C': 15},
    'WK3': {'A': 55, 'B': 25, 'C': 20},
    'WK4': {'A': 65, 'B': 25, 'C': 10},
    'WK5': {'A': 60, 'B': 30, 'C': 10},
}
election.start(votes=votes)

sitze  = SeatDistributor().run(election)                   # {'A': 6, 'B': 3, 'C': 1}
anzahl = ConstituencyCountDeterminer().run(election, sitze) # {'A': 3, 'B': 2, 'C': 0}
zuordnung = ConstituencyAssigner(seed=42).run(election, anzahl)
print(zuordnung)  # {'WK1': 'A', 'WK2': 'B', 'WK3': 'A', 'WK4': 'A', 'WK5': 'B'}
```