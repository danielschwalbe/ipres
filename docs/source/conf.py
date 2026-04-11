# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'IPRES – (Iterative Proportional Representation) Election Simulation'
copyright = '2026, Daniel Schwalbe'
author = 'Daniel Schwalbe'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",   # Google-style Docstrings
    "sphinx.ext.autodoc",    # Docstrings aus Quellcode lesen
    "sphinx.ext.intersphinx",    # Links zu externer Doku (numpy, pandas, ...)
    "myst_parser",           # Markdown-Dateien in Sphinx einbinden
]

myst_enable_extensions = ["colon_fence"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}

templates_path = ['_templates']
exclude_patterns = ["**/.ipynb_checkpoints", "doc/en/*", "doc/strategies_for_better_modelling_voters_behavior.md"]

locale_dirs = ['locales/']
gettext_compact = False

suppress_warnings = ["autodoc.duplicate_object", "myst.xref_missing", "toc.not_readable"]


def _on_builder_inited(app):
    if app.config.language == 'de':
        app.tags.add('de_build')
        app.config.exclude_patterns.append('en')
    else:
        app.tags.add('en_build')
        app.config.exclude_patterns.append('de')


def setup(app):
    app.connect('builder-inited', _on_builder_inited)


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'furo'
html_theme = 'sphinx_rtd_theme'
#html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

add_module_names = False
autodoc_typehints_format = "short"

autodoc_type_aliases = {
    "ipres.constituencies_config.ConstituenciesConfig": "ConstituenciesConfig",
    "ipres.super_majority_margin.SuperMajorityMargin": "SuperMajorityMargin",
    "ipres.election_round.DrawLotsStrategy": "DrawLotsStrategy",
    "ipres.election_config.ConstituencyRepresentation": "ConstituencyRepresentation",
    "ipres.election_config.Language": "Language",
}

autodoc_typehints = "description"