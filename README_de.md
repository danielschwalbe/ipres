🇬🇧 [English](README.md) | 🇩🇪 Deutsch

![Tests](https://github.com/danielschwalbe/ipres/actions/workflows/ci.yml/badge.svg)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD)

# IPRES – Election Simulation

IPRES ist eine Python-Bibliothek zur Simulation eines verbesserten Wahlverfahrens für den Deutschen Bundestag. Sie dient dazu, das Verfahren auf Korrektheit zu testen, Fehler und Inkonsistenzen zu finden und das Verfahren zu demonstrieren.

---

## Das Wahlverfahren

IPRES simuliert ein verbessertes Verhältniswahlverfahren: Durch iterative Wahlgänge wird garantiert eine Gewinnerpartei ermittelt, während die Opposition proportional repräsentiert bleibt. Jeder Wahlkreis ist im Parlament vertreten.

Eine ausführliche Beschreibung des Verfahrens findet sich in der [Einführung](docs/source/de/einfuehrung.md) oder in der Dokumentation ([online](https://danielschwalbe.github.io/ipres/de/) | [lokal](docs/build/html/de/index.html)).

**Hinweis**: Die lokale HTML-Dokumentation muss einmalig gebaut werden (siehe [Dokumentation](#dokumentation)) und enthält neben den Konzepten auch die API-Referenz.

---

## Die Simulation

### Projektstruktur

```
ipres/
├── src/ipres/          # Kernbibliothek
│   ├── election.py             # Hauptwahlablauf
│   ├── election_round.py       # Rundenlogik (Ballot, DrawOfLots)
│   ├── ballot.py               # Stimmabgabe und -auswertung
│   ├── election_config.py      # Wahlkonfiguration
│   ├── vote_matrix.py          # Stimmenmatrix
│   ├── allocation.py           # Wahlkreis-Zuteilungsstrategien
│   ├── apportionment.py        # Sitzzuteilung (Sainte-Laguë etc.)
│   └── ...
├── notebooks/          # Jupyter Notebooks zur Demonstration
│   ├── de/             # Deutsche Notebooks
│   └── en/             # Englische Notebooks
├── tests/              # Unit Tests
├── docs/               # Sphinx-Dokumentation (API-Referenz + Konzepte)
├── data/
│   ├── bundestagswahl/ # Echte BTW-Ergebnisse (1949–2025, kerg-Format)
│   └── examples/       # Beispieldaten
├── concept/            # Ursprüngliches Konzeptdokument (möglicherweise veraltet)
└── attic/              # Notizen und Schnipsel (nicht Teil des Projekts)
```

### Notebooks

Die Jupyter Notebooks zeigen das Verfahren anhand konkreter Beispiele. Einstiegspunkte:

| Notebook | Inhalt | |
|----------|--------|---|
| [`kurzuebersicht.ipynb`](notebooks/de/kurzuebersicht.ipynb) | Vollständiger Ablauf an einem kleinen Beispiel | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fde%2Fkurzuebersicht.ipynb) |
| [`iterative_verhältniswahl.ipynb`](notebooks/de/iterative_verhältniswahl.ipynb) | Wahlverfahren Schritt für Schritt | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fde%2Fiterative_verh%C3%A4ltniswahl.ipynb) |
| [`bundestagswahl.ipynb`](notebooks/de/bundestagswahl.ipynb) | Simulation mit echten Bundestagswahl-Daten | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fde%2Fbundestagswahl.ipynb) |
| [`anwendungsbeispiel.ipynb`](notebooks/de/anwendungsbeispiel.ipynb) | Generische Wahl mit interaktiver Konfiguration | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fde%2Fanwendungsbeispiel.ipynb) |
| [`wahlauswertung.ipynb`](notebooks/de/wahlauswertung.ipynb) | Sitzverteilung und Wahlkreiszuordnung | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fde%2Fwahlauswertung.ipynb) |
| [`spezialfälle.ipynb`](notebooks/de/spezialfälle.ipynb) | Grenzfälle und Sondersituationen | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fde%2Fspezialf%C3%A4lle.ipynb) |

Die Notebooks können direkt im Browser ausgeführt werden – ohne lokale Installation. Ein Klick auf den [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD) öffnet das jeweilige Notebook in [Binder](https://mybinder.org), einer kostenlosen Plattform für interaktive Jupyter-Umgebungen. Beim ersten Start wird die Umgebung einmalig aufgebaut, was 1–5 Minuten dauern kann.

Weitere Notebooks zu Konfigurationsdetails: `globale_konfiguration.ipynb`, `Parteien.ipynb`, `wahlkreise.ipynb`, `wahlteilnehmer.ipynb`, `vote_matrix.ipynb`

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Tests ausführen

```bash
source .venv/bin/activate
pytest
```

### Mutation Testing

Mutation Testing prüft die Qualität der Unit Tests, indem kleine Änderungen (Mutationen) im Quellcode vorgenommen werden. Überlebt eine Mutation (die Tests schlagen nicht fehl), deutet das auf eine Lücke in den Tests hin.

**Lokal ausführen:**

```bash
source .venv/bin/activate

# Alle Module testen
mutmut run

# Nur ein bestimmtes Modul testen (schneller)
mutmut run --paths-to-mutate src/ipres/apportionment.py

# Ergebnisse anzeigen
mutmut results

# Details zu überlebenden Mutanten
mutmut show <id>

# HTML-Report generieren (optional)
mutmut html
```

**In GitHub Actions:**

Der Workflow kann manuell über die GitHub Actions UI ausgeführt werden:
1. Gehe zu "Actions" → "Mutation Testing"
2. Klicke auf "Run workflow"
3. Optional: Gib ein spezifisches Modul an (z.B. `apportionment.py`)
4. Starte den Workflow

Die Ergebnisse und der `.mutmut-cache` werden als Artefakt gespeichert.

### Dokumentation

Die API-Dokumentation wird mit Sphinx generiert. Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

Englische Dokumentation bauen:
```bash
cd docs && make html
```

Deutsche Dokumentation bauen:
```bash
cd docs && sphinx-build -b html -D language=de source build/html/de
```

Die fertige Dokumentation liegt in `docs/build/html/index.html` (Englisch) bzw. `docs/build/html/de/index.html` (Deutsch) und kann direkt im Browser geöffnet werden.

Der Build-Prozess wird bei jedem Push auf den `main`-Branch automatisch ausgeführt. Die Dokumentation steht daher stets aktuell online zur Verfügung: [Englisch](https://danielschwalbe.github.io/ipres/) | [Deutsch](https://danielschwalbe.github.io/ipres/de/).

Detaillierter Übersetzungsfluss: [TRANSLATION_de.md](TRANSLATION_de.md)

### Schnellstart

```python
import pandas as pd
from ipres import Election, ElectionConfig
from ipres.constituencies_config import ConstituenciesConfig

cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
    'constituency_name': ['WK1', 'WK2'],
    'constituency_size': [50000, 60000],
    'turnout_percent': [75.0, 80.0],
}))

config = ElectionConfig(
    constituencies_config=cc,
    participating_parties=['A', 'B', 'C'],
    seed=42,
)

election = Election(electionConfig=config)
result = election.run()

print(f"Gewinner: {result.getWinner().name}")
```

---
## Disclaimer
Dieses Projekt ist in zwei kurzen Urlauben mit intensiver KI-Unterstützung entstanden. Der Autor hat einen C++/Java-Hintergrund und ist kein Python-Entwickler — das sieht man dem Code stellenweise auch an. Nichtsdestotrotz ist der eigentliche Zweck erfüllt: das Wahlverfahren zu verifizieren und zu demonstrieren. Und es ist interessant zu sehen, wie weit man mithilfe von KI auch in fremden Programmiersprachen kommt.

## Copyright & Lizenz

Copyright © 2025 Daniel Schwalbe

Veröffentlicht unter der [MIT-Lizenz](LICENSE).