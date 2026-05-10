# Unit Tests
- Source the .venv to run unit tests: `source .venv/bin/activate && pytest`
- Single test file: `pytest tests/AllocationTests.py`
- With coverage: `pytest --cov=ipres --cov-report=term-missing`

# Documentation
- Build PDF (German electoral procedure): `cd docs/wahlverfahren/de && make pdf` → output in `dist/`
- Build Sphinx HTML: `cd docs && make html` → output in `build/html/`

# Language
- Document the entire code in English
- Notebooks and Readmes in German and English
- Commit messages in English
- German user documentation (Notebooks and Readmes) is the source of truth from the author's perspective. Translate from there to English. 
- Keep the user documentation always consistent.
- Present English to the audience as default.
- When translating from German to English, internally do a reverse translation per default and compare the results. In case of differences, correct the translation until a match is achieved.
- In case of unclear translations, prompt the author to clarify. 
