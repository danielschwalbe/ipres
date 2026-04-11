# Wahlkreis-Zuteilungsstrategien (Constituency Allocation Strategies)

Dieses Dokument beschreibt die implementierten Strategien zur Zuteilung von Wahlkreisen an Parteien basierend auf Wichtigkeitsmetriken und Quoten.

## Überblick

Das Modul `ipres.allocation` bietet verschiedene Strategien zur Beantwortung der Frage: **Welche Partei soll welchen Wahlkreis im Parlament repräsentieren?**

Dies ist relevant für:
- First-Past-The-Post (FPTP) Systeme
- Gemischte Wahlsysteme (z.B. Bundestag mit Direktmandaten)
- Strategische Wahlkreisverteilung basierend auf Partei-Stärken

## Implementierte Strategien

### 1. Greedy Allocation Strategy

#### Algorithmus
```
1. Berechne für alle (Wahlkreis, Partei)-Paare die Wichtigkeit
2. Sortiere alle Paare nach Wichtigkeit (absteigend)
3. Weise iterativ das Paar mit höchster Wichtigkeit zu
4. Respektiere dabei Partei-Quoten
5. Wiederhole bis alle Wahlkreise verteilt sind
```

#### Eigenschaften
- **Zeitkomplexität:** O(n log n), wobei n = Anzahl Wahlkreise × Anzahl Parteien
- **Garantie:** ⚠️ **NICHT optimal!** Greedy ist eine Heuristik, die gute, aber nicht immer optimale Lösungen findet
- **Vorteil:** Einfach, schnell, intuitiv, oft nahe am Optimum
- **Nachteil:**
  - Kann zu suboptimalen Lösungen führen (siehe Beispiel unten)
  - Kann zu "unfairen" Situationen führen, wo Parteien sich benachteiligt fühlen

#### Verwendung

```python
from ipres.allocation import allocate_constituencies_greedy
from ipres.vote_matrix_analyzer import getConstituencyImportanceMatrix

# Wichtigkeitsmatrix berechnen
importance_matrix = getConstituencyImportanceMatrix(relative_votes)

# Quoten definieren
quotas = {"CDU": 100, "SPD": 80, "Grüne": 50}  # Summe muss = Anzahl Wahlkreise sein

# Greedy-Zuteilung
allocation = allocate_constituencies_greedy(
    importance_matrix,
    quotas,
    rng=np.random.default_rng(42)  # Für Tie-Breaking
)

# Ergebnis: {"Wahlkreis 001": "CDU", "Wahlkreis 002": "SPD", ...}
```

#### Gegenbeispiel: Greedy ist nicht optimal

```python
import pandas as pd
import numpy as np
from ipres.allocation import allocate_constituencies_greedy

# Beispiel wo Greedy suboptimal ist
importance_matrix = pd.DataFrame({
    "A": [7, 5, 1, 1],
    "B": [5, 1, 5, 1],
    "C": [1, 6, 4, 5]
}, index=["WK1", "WK2", "WK3", "WK4"])

quotas = {"A": 2, "B": 1, "C": 1}

allocation = allocate_constituencies_greedy(
    importance_matrix, quotas, np.random.default_rng(42)
)

# Greedy Ergebnis (Score: 19):
#   A: WK1(7), WK4(1)  = 8
#   B: WK3(5)          = 5
#   C: WK2(6)          = 6

# Optimales Ergebnis (Score: 22):
#   A: WK1(7), WK2(5)  = 12
#   B: WK3(5)          = 5
#   C: WK4(5)          = 5

# Greedy ist 13.6% schlechter!
```

**Warum schlägt Greedy fehl?**
- Greedy nimmt WK2→C (6) weil es besser als WK2→A (5) erscheint
- Aber WK4→C (5) ist fast genauso gut
- Während WK2→A (5) >> WK4→A (1)
- Greedy sieht diese späteren Konsequenzen nicht

Für eine **optimale** Lösung, siehe `OptimalAllocationStrategy` (basierend auf Linear Programming).

### 2. Optimal Allocation Strategy (Hungarian Algorithm)

#### Algorithmus
```
1. Erstelle erweiterte Kostenmatrix:
   - Zeilen = Wahlkreise
   - Spalten = "Slots" (jede Partei bekommt quota viele Slots)
   - Kosten = -importance (negiert, weil wir maximieren wollen)

2. Löse Assignment Problem mit Hungarian Algorithm (linear_sum_assignment)
   - Findet optimale 1-zu-1 Zuordnung: jeder Wahlkreis zu genau einem Slot
   - Minimiert Gesamtkosten (= maximiert Gesamt-Wichtigkeit)

3. Mappe Slots zurück zu Parteien
```

#### Eigenschaften
- **Zeitkomplexität:** O(n³), wobei n = Anzahl Wahlkreise
- **Garantie:** ✓ **Provably optimal!** Findet die beste mögliche Zuteilung
- **Vorteil:**
  - Garantiert maximale Gesamt-Wichtigkeit
  - Deterministisch (bei eindeutiger Lösung)
  - Mathematisch fundiert
- **Nachteil:**
  - Langsamer als Greedy (aber für realistische Größen <1000 Wahlkreise kein Problem)
  - Komplexere Implementierung
  - Bei Ties (gleiche importance) ist Ergebnis nicht deterministisch

#### Verwendung
```python
from ipres.allocation import allocate_constituencies_optimal

# Identische Parameter wie bei Greedy
allocation = allocate_constituencies_optimal(
    importance_matrix,
    quotas
    # Kein rng nötig - Algorithmus ist deterministisch
)
```

#### Wie funktioniert das Slot-System?

**Problem:** Hungarian Algorithm kann nur 1-zu-1 Zuordnungen. Aber wir brauchen many-to-one (viele Wahlkreise → wenige Parteien).

**Lösung:** Erstelle mehrere "Slots" pro Partei:

```python
parties = ["A", "B", "C"]
quotas = {"A": 2, "B": 1, "C": 1}

# Slots erstellen:
slot_to_party = ["A", "A", "B", "C"]  # A erscheint 2x, B und C je 1x

# Jetzt haben wir 4 Wahlkreise → 4 Slots (1-zu-1 möglich!)
```

Die Kostenmatrix sieht dann so aus:
```
           Slot0(A)  Slot1(A)  Slot2(B)  Slot3(C)
WK1           -7        -7        -5        -1
WK2           -5        -5        -1        -6
WK3           -1        -1        -5        -4
WK4           -1        -1        -1        -5
```

Hungarian Algorithm findet optimale Zuordnung, z.B.:
- WK1 → Slot0(A)
- WK2 → Slot1(A)
- WK3 → Slot2(B)
- WK4 → Slot3(C)

Ergebnis: `{"WK1": "A", "WK2": "A", "WK3": "B", "WK4": "C"}`

### 3. Stable Matching Allocation Strategy

#### Algorithmus (modifizierter Gale-Shapley)
```
1. Erstelle Präferenz-Listen:
   - Jede Partei ranked Wahlkreise nach Wichtigkeit
   - Jeder Wahlkreis ranked Parteien nach deren Wichtigkeit für ihn

2. Iterativer Matching-Prozess:
   - Wahlkreise "bewerben" sich bei ihrer bevorzugten Partei
   - Parteien akzeptieren/lehnen ab basierend auf:
     * Aktuelle Zuweisungen
     * Quote (Kapazität)
     * Präferenz
   - Abgelehnte Wahlkreise bewerben sich bei nächster Präferenz

3. Terminierung wenn stabile Zuteilung gefunden
```

#### Eigenschaften
- **Zeitkomplexität:** O(n²), wobei n = Anzahl Wahlkreise
- **Garantie:** Keine "Blocking Pairs" - stabile Zuteilung
- **Vorteil:** Game-theoretisch fundiert, garantiert faire Verteilung
- **Nachteil:** Komplexer, kann niedrigere Gesamt-Wichtigkeit haben als Greedy

#### Was ist ein "Blocking Pair"?
Ein Blocking Pair existiert, wenn:
- Wahlkreis X ist Partei A zugewiesen
- Partei B würde X lieber haben als einen ihrer aktuellen Wahlkreise
- X würde lieber zu B gehören (B schätzt X höher als A)

→ Beide würden den Tausch bevorzugen = instabile Situation

**Stable Matching garantiert: Keine solchen Paare existieren!**

#### Verwendung
```python
from ipres.allocation import allocate_constituencies_stable

# Identische Parameter wie bei Greedy
allocation = allocate_constituencies_stable(
    importance_matrix,
    quotas,
    rng=np.random.default_rng(42)
)
```

## Vergleich der Strategien

| Aspekt | Greedy | Optimal (Hungarian) | Stable Matching |
|--------|--------|---------------------|-----------------|
| **Optimierungsziel** | Hohe Gesamt-Wichtigkeit (Heuristik) | Maximale Gesamt-Wichtigkeit | Stabile Zuteilung |
| **Optimalität** | ⚠️ Nicht optimal (kann 10-15% schlechter sein) | ✓ **Provably optimal** | Optimal für Stabilität |
| **Komplexität** | O(n log n) | O(n³) | O(n²) |
| **Geschwindigkeit** | Schnellste | Mittel | Langsamste |
| **Fairness** | Kann unfair sein | Maximiert Gesamt-Nutzen | Garantiert fair |
| **Verständlichkeit** | Sehr intuitiv | Erfordert Algorithmus-Verständnis | Erfordert Konzept-Verständnis |
| **Anwendungsfall** | Schnelle Heuristik | Benchmark / Optimale Lösung | Dezentrale Verhandlung |

## Wann welche Strategie?

### Verwende **Greedy** wenn:
- Geschwindigkeit wichtig ist
- Eine gute (aber nicht perfekte) Lösung ausreicht
- Einfache Erklärbarkeit wichtig ist
- Die Datengröße sehr groß ist (>1000 Wahlkreise)

### Verwende **Optimal (Hungarian)** wenn:
- Die **beste** Lösung garantiert werden soll
- Benchmarking / Vergleich mit anderen Strategien
- Realistische Größen (<1000 Wahlkreise) - Performance kein Problem
- Maximierung des Gesamt-Nutzens das Ziel ist

### Verwende **Stable Matching** wenn:
- Fairness/Stabilität wichtiger als Effizienz ist
- Parteien die Zuteilung akzeptieren müssen
- Akademische Analyse/Publikation geplant ist
- Game-theoretische Eigenschaften relevant sind

## Literatur und Referenzen

### Hungarian Algorithm / Assignment Problem

**Original-Paper:**
- Kuhn, H. W. (1955). "The Hungarian Method for the assignment problem"
  - Naval Research Logistics Quarterly, 2(1-2), 83-97
  - https://doi.org/10.1002/nav.3800020109
  - Das grundlegende Paper (historisch wichtig)

- Munkres, J. (1957). "Algorithms for the Assignment and Transportation Problems"
  - Journal of the Society for Industrial and Applied Mathematics, 5(1), 32-38
  - https://doi.org/10.1137/0105003
  - Verbesserte Version des Algorithmus

**Wikipedia:**
- Englisch: https://en.wikipedia.org/wiki/Hungarian_algorithm
- Deutsch: https://de.wikipedia.org/wiki/Ungarische_Methode
- Assignment Problem: https://en.wikipedia.org/wiki/Assignment_problem

**Tutorials & Visualisierungen:**
- "The Hungarian Algorithm" (brillante Erklärung mit Bildern):
  - https://www.hungarianalgorithm.com/

- Brilliant.org Interactive Tutorial:
  - https://brilliant.org/wiki/hungarian-matching/

- YouTube Tutorial von Tushar Roy:
  - "Hungarian Algorithm for Assignment Problem"
  - https://www.youtube.com/watch?v=dQDZNHwuuOY

**Implementation (scipy):**
- scipy.optimize.linear_sum_assignment Documentation:
  - https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linear_sum_assignment.html
  - Verwendet moderne O(n³) Implementation

**Bücher:**
- Papadimitriou, C. H., & Steiglitz, K. (1998). "Combinatorial Optimization: Algorithms and Complexity"
  - Kapitel 11: The Assignment Problem
  - ISBN: 978-0486402581
  - Umfassende mathematische Behandlung

- Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2009). "Introduction to Algorithms" (3rd ed.)
  - Kapitel 26: Maximum Flow (enthält auch Assignment Problem)
  - ISBN: 978-0262033848
  - Das Standard-Lehrbuch

**Linear Programming Connection:**
- Schrijver, A. (2003). "Combinatorial Optimization: Polyhedra and Efficiency"
  - Volume A, Kapitel 17: Bipartite Matching
  - ISBN: 978-3540443896
  - Sehr theoretisch, aber umfassend

### Grundlagen: Stable Matching

**Original-Paper (frei verfügbar):**
- Gale, D., & Shapley, L. S. (1962). "College Admissions and the Stability of Marriage"
  - https://www.jstor.org/stable/2312726
  - Das grundlegende Paper - sehr lesbar!

**Wikipedia:**
- Englisch: https://en.wikipedia.org/wiki/Gale%E2%80%93Shapley_algorithm
- Deutsch: https://de.wikipedia.org/wiki/Gale-Shapley-Algorithmus

**Interactive Visualisierung:**
- https://algorithm-visualizer.org/branch-and-bound/stable-marriage-problem

**Tutorial (Cornell University):**
- https://www.cs.cornell.edu/~bindel/class/cs322-s06/stable.pdf

### Grundlagen: Greedy Algorithms

**Wikipedia:**
- Englisch: https://en.wikipedia.org/wiki/Greedy_algorithm
- Deutsch: https://de.wikipedia.org/wiki/Greedy-Algorithmus

**Assignment Problem:**
- https://en.wikipedia.org/wiki/Assignment_problem

### Many-to-One Matching mit Quoten

**Direkt relevant für unsere Implementierung:**
- "Many-to-One Stable Matching: Geometry and Fairness" (2013)
  - https://arxiv.org/abs/1310.4628
  - Erklärt genau die Variante mit Quoten!

**Matching Markets:**
- Roth, A. E., & Sotomayor, M. (1990). "Two-Sided Matching: A Study in Game-Theoretic Modeling and Analysis"
  - https://www.nber.org/papers/w1392 (Working Paper Version)
  - Das Standardwerk für Matching-Theorie

**Alvin Roth's Papers (Nobelpreisträger):**
- https://web.stanford.edu/~alroth/papers/
- Viele Papers frei verfügbar

### Warum beide oft gleiche Ergebnisse liefern

**Theoretical Background:**
- Kelso, A. S., & Crawford, V. P. (1982). "Job Matching, Coalition Formation, and Gross Substitutes"
  - https://www.jstor.org/stable/2526954
  - Erklärt, wann Greedy bereits stabile Lösungen findet

### Bücher (gedruckt)

**Für Greedy Algorithms:**
- Kleinberg, J., & Tardos, É. (2005). "Algorithm Design"
  - Kapitel 1: Greedy Algorithms
  - ISBN: 978-0321295354

**Für Stable Matching:**
- Roth, A. E., & Sotomayor, M. (1990). "Two-Sided Matching"
  - ISBN: 978-0521437882
  - Das umfassende Standardwerk

## Beispiele

### Einfaches Beispiel

```python
import numpy as np
import pandas as pd
from ipres.allocation import (
    allocate_constituencies_greedy,
    allocate_constituencies_stable
)

# Importance Matrix erstellen
importance_matrix = pd.DataFrame({
    "Partei_A": [0.60, 0.55, 0.20, 0.15],
    "Partei_B": [0.58, 0.30, 0.57, 0.56]
}, index=["WK1", "WK2", "WK3", "WK4"])

quotas = {"Partei_A": 2, "Partei_B": 2}

# Beide Strategien ausprobieren
greedy_result = allocate_constituencies_greedy(
    importance_matrix, quotas, np.random.default_rng(42)
)
stable_result = allocate_constituencies_stable(
    importance_matrix, quotas, np.random.default_rng(42)
)

print("Greedy:", greedy_result)
print("Stable:", stable_result)
```

### Bundestag-ähnliches Szenario

```python
from ipres.ballot import Ballot
from ipres.vote_matrix_analyzer import getConstituencyImportanceMatrix

# Wahl durchführen
ballot = Ballot.run(
    constituencies_config=wahlkreise_bundestag,
    contestants=parteien,
    probabilities={"CDU": 30, "SPD": 25, "Grüne": 20, ...},
    rng=np.random.default_rng(42)
)

# Importance Matrix berechnen
relative_votes = ballot.getRelativeVoteMatrix()
importance_matrix = getConstituencyImportanceMatrix(relative_votes)

# Quoten basierend auf Sitzzahl
quotas = {
    "CDU": 100,
    "SPD": 80,
    "Grüne": 50,
    "Linke": 30,
    "AFD": 25,
    "FDP": 14
}  # Summe = 299 (Anzahl Wahlkreise)

# Zuteilung
allocation = allocate_constituencies_greedy(importance_matrix, quotas)

# Analyse
for party in quotas.keys():
    assigned = [wk for wk, p in allocation.items() if p == party]
    print(f"{party}: {len(assigned)} Wahlkreise")
```

## Objektorientierte API

Für erweiterte Anwendungen kann die OO-API verwendet werden:

```python
from ipres.allocation import GreedyAllocationStrategy, StableMatchingAllocationStrategy

# Strategy Pattern
strategy = GreedyAllocationStrategy()  # oder StableMatchingAllocationStrategy()
allocation = strategy.allocate(importance_matrix, quotas, rng)
```

Dies ermöglicht:
- Einfaches Wechseln zwischen Strategien
- Implementierung eigener Strategien durch Ableitung von `ConstituencyAllocationStrategy`
- Dependency Injection in größeren Systemen

## Tests

Umfassende Unit-Tests finden sich in `tests/AllocationTests.py`:
- Grundlegende Funktionalität
- Quotenvalidierung
- Determinismus (mit Seeds)
- Stabilitätsprüfung
- Realistische Szenarien (299 Wahlkreise, 6 Parteien)

Tests ausführen:
```bash
pytest tests/AllocationTests.py -v
```

## Zukünftige Erweiterungen

Mögliche weitere Strategien:
- **Max-Flow basierte Optimierung** (maximale gewichtete Zuteilung)
- **Auction Algorithms** (iterative Bieter-Mechanismen)
- **Proportional Allocation** (basierend auf Stimmanteilen)
- **Geographic Constraints** (benachbarte Wahlkreise bevorzugen)

## Autor und Lizenz

Teil des `ipres` Packages (Election Simulation)
- Autor: Daniel
- Lizenz: MIT
- Version: 0.1.0

## Fragen?

Bei Fragen oder Verbesserungsvorschlägen bitte ein Issue auf GitHub erstellen.
