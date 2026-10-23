🇬🇧 English | 🇩🇪 [Deutsch](README_de.md)

![Tests](https://github.com/danielschwalbe/ipres/actions/workflows/ci.yml/badge.svg)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD)

# IPRES – Iterative Proportional Representation Election Simulation

IPRES is a Python library for simulating an improved electoral procedure for the German Bundestag. It is designed to test the procedure for correctness, identify errors and inconsistencies, and demonstrate how it works.

---

## The Electoral Procedure

IPRES simulates an improved proportional electoral procedure: iterative rounds of voting guarantee that a winning party is determined, while the opposition remains proportionally represented. Every constituency is guaranteed a seat in parliament.

A detailed description of the procedure can be found in the [Introduction](docs/source/en/introduction.md) or in the documentation ([online](https://danielschwalbe.github.io/ipres/) | [local](docs/build/html/index.html)).

**Note**: The local HTML documentation must be built once (see [Documentation](#documentation)) and covers both the concepts and the API reference.

---

## The Simulation

### Project Structure

```
ipres/
├── src/ipres/          # Core library
│   ├── election.py             # Main election flow
│   ├── election_round.py       # Round logic (Ballot, DrawOfLots)
│   ├── ballot.py               # Voting and vote evaluation
│   ├── election_config.py      # Election configuration
│   ├── vote_matrix.py          # Vote matrix
│   ├── allocation.py           # Constituency allocation strategies
│   ├── apportionment.py        # Seat apportionment (Sainte-Laguë etc.)
│   └── ...
├── notebooks/          # Jupyter Notebooks for demonstration
│   ├── de/             # German notebooks
│   └── en/             # English notebooks
├── tests/              # Unit tests
├── docs/               # Sphinx documentation (API reference + concepts)
├── data/
│   ├── bundestagswahl/ # Real federal election results (1949–2025, kerg format)
│   └── examples/       # Example data
├── concept/            # Original concept document (may be outdated)
└── attic/              # Notes and snippets (not part of the project)
```

### Notebooks

The Jupyter Notebooks demonstrate the procedure using concrete examples. Entry points:

| Notebook | Content | |
|----------|---------|---|
| [`quick_overview.ipynb`](notebooks/en/quick_overview.ipynb) | Complete walkthrough with a small example | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fen%2Fquick_overview.ipynb) |
| [`iterative_proportional_election.ipynb`](notebooks/en/iterative_proportional_election.ipynb) | Electoral procedure step by step | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fen%2Fiterative_proportional_election.ipynb) |
| [`federal_election.ipynb`](notebooks/en/federal_election.ipynb) | Simulation using real federal election data | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fen%2Ffederal_election.ipynb) |
| [`application_example.ipynb`](notebooks/en/application_example.ipynb) | Generic election with interactive configuration | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fen%2Fapplication_example.ipynb) |
| [`election_evaluation.ipynb`](notebooks/en/election_evaluation.ipynb) | Seat allocation and constituency assignment | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fen%2Felection_evaluation.ipynb) |
| [`special_cases.ipynb`](notebooks/en/special_cases.ipynb) | Edge cases and special situations | [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD?labpath=notebooks%2Fen%2Fspecial_cases.ipynb) |

The notebooks can be run directly in the browser — without local installation. Click the [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/danielschwalbe/ipres/HEAD) to open the respective notebook in [Binder](https://mybinder.org), a free platform for interactive Jupyter environments. On the first launch, the environment is built once, which may take 1–5 minutes.

Further notebooks covering configuration details: `global_configuration.ipynb`, `contestant.ipynb`, `vote_matrix.ipynb`

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Running Tests

```bash
source .venv/bin/activate
pytest
```

### Mutation Testing

Mutation testing validates the quality of unit tests by introducing small changes (mutations) to the source code. If a mutation survives (the tests do not fail), this indicates a gap in test coverage.

**Run locally:**

```bash
source .venv/bin/activate

# Test all modules
mutmut run

# Test only a specific module (faster)
mutmut run --paths-to-mutate src/ipres/apportionment.py

# Show results
mutmut results

# Show details of surviving mutants
mutmut show <id>

# Generate HTML report (optional)
mutmut html
```

**In GitHub Actions:**

The workflow can be triggered manually via the GitHub Actions UI:
1. Go to "Actions" → "Mutation Testing"
2. Click "Run workflow"
3. Optional: Specify a specific module (e.g., `apportionment.py`)
4. Start the workflow

Results and the `.mutmut-cache` are saved as artifacts.

### Documentation

The API documentation is generated with Sphinx. Install all dependencies:

```bash
pip install -r requirements.txt
```

Build English documentation:
```bash
cd docs && make html
```

Build German documentation:
```bash
cd docs && sphinx-build -b html -D language=de source build/html/de
```

The finished documentation is located at `docs/build/html/index.html` (English) and `docs/build/html/de/index.html` (German) and can be opened directly in a browser.

The build process is triggered automatically on every push to the `main` branch. The documentation is therefore always up to date and available online: [English](https://danielschwalbe.github.io/ipres/) | [German](https://danielschwalbe.github.io/ipres/de/).

For the detailed translation workflow see [TRANSLATION.md](TRANSLATION.md).

### Quick Start

```python
import pandas as pd
from ipres import Election, ElectionConfig
from ipres.constituencies_config import ConstituenciesConfig

cc = ConstituenciesConfig.from_dataframe(pd.DataFrame({
    'constituency_name': ['C1', 'C2'],
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

print(f"Winner: {result.getWinner().name}")
```

---

## Disclaimer

This project was built during two short holidays with intensive AI assistance. The author has a C++/Java background and is not a Python developer — which shows in the code here and there. Nevertheless, the actual purpose has been achieved: to verify and demonstrate the electoral procedure. And it is interesting to see how far one can get with AI even in an unfamiliar programming language.

---

## Copyright & License

Copyright © 2025 Daniel Schwalbe

Released under the [MIT License](LICENSE).
