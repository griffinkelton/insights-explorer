"""Sphinx configuration for GA4 Insight Explorer API documentation."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "GA4 Insight Explorer"
copyright = "2026"
author = "Griffin Kelton"
release = "1.7.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_title = "GA4 Insight Explorer Docs"
html_static_path = ["_static"]

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

# Intersphinx
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}
