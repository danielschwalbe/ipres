🇬🇧 [English](README.md) | 🇩🇪 Deutsch

![Tests](https://github.com/danielschwalbe/ipres/actions/workflows/ci.yml/badge.svg)

# IPRES – Election Simulation

IPRES ist eine Python-Bibliothek zur Simulation eines verbesserten Wahlverfahrens für den Deutschen Bundestag. Sie dient dazu, das Verfahren auf Korrektheit zu testen, Fehler und Inkonsistenzen zu finden und das Verfahren zu demonstrieren.

---

## Das Wahlverfahren

IPRES simuliert ein verbessertes Verhältniswahlverfahren: Durch iterative Wahlgänge wird garantiert eine Gewinnerpartei ermittelt, während die Opposition proportional repräsentiert bleibt. Jeder Wahlkreis ist im Parlament vertreten.

Eine ausführliche Beschreibung des Verfahrens findet sich in der [Einführung](docs/source/de/einfuehrung.md) oder in der [HTML-Dokumentation](docs/build/html/de/index.html).

**Hinweis**: Die HTML-Dokumentation muss einmalig gebaut werden (siehe [Dokumentation](#dokumentation)) und enthält neben den Konzepten auch die API-Referenz.

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

| Notebook | Inhalt |
|----------|--------|
| [`kurzuebersicht.ipynb`](notebooks/de/kurzuebersicht.ipynb) | Vollständiger Ablauf an einem kleinen Beispiel |
| [`iterative_verhältniswahl.ipynb`](notebooks/de/iterative_verhältniswahl.ipynb) | Wahlverfahren Schritt für Schritt |
| [`bundestagswahl.ipynb`](notebooks/de/bundestagswahl.ipynb) | Simulation mit echten Bundestagswahl-Daten |
| [`anwendungsbeispiel.ipynb`](notebooks/de/anwendungsbeispiel.ipynb) | Generische Wahl mit interaktiver Konfiguration |
| [`wahlauswertung.ipynb`](notebooks/de/wahlauswertung.ipynb) | Sitzverteilung und Wahlkreiszuordnung |
| [`spezialfälle.ipynb`](notebooks/de/spezialfälle.ipynb) | Grenzfälle und Sondersituationen |

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

Die fertige Dokumentation liegt in `docs/build/html/index.html` (Englisch) bzw. `docs/build/html/de/index.html` (Deutsch) und kann direkt im Browser geöffnet werden. Detaillierter Übersetzungsfluss: [TRANSLATION_de.md](TRANSLATION_de.md)

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