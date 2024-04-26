# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
sys.path.insert(0, os.path.abspath('../'))

project = 'science_jubilee'
copyright = '2023, Machine Agency'
author = 'Machine Agency'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'autoapi.extension',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = []

# autoapi info
autoapi_dirs = ['../../science_jubilee']
# autoapi_add_toctree_entry = False



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

html_theme_options = {
    "use_edit_page_button": True,
}

html_context = {
    # "github_url": "https://github.com", # or your GitHub Enterprise site
    "github_user": "machineagency",
    "github_repo": "science_jubilee",
    "github_version": "main",
    "doc_path": "docs/source",
}
