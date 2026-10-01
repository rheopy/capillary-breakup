import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "caber"
author = "Marco Caggioni"
release = "0.1.0"

extensions = ["myst_parser", "sphinx.ext.autodoc", "sphinx.ext.napoleon"]
myst_enable_extensions = ["dollarmath"]
templates_path = ["_templates"]
exclude_patterns = ["_build"]
html_theme = "sphinx_rtd_theme"

autodoc_member_order = "bysource"
