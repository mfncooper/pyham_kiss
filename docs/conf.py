# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import kiss


# -- Project information -----------------------------------------------------

project = 'PyHam KISS'
copyright = '2024-2025, Martin F N Cooper. All rights reserved'
author = 'Martin F N Cooper'
release = kiss.__version__
version = release


# -- General configuration ---------------------------------------------------

extensions = [
    'autoapi.extension'
]
autoapi_dirs = ['../kiss']
autoapi_options = [
    'members',
    'show-inheritance',
    'show-module-summary',
    'imported-members'
]

templates_path = ['_templates']

rst_prolog = """
.. meta::
   :author: Martin F N Cooper
   :description: A client implementation for the KISS TNC protocol,
      providing send and receive capability via a TCP/IP connection.
"""


# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = [ 'css/bmc.css' ]
html_theme_options = {
    'prev_next_buttons_location': 'none'
}
html_show_sourcelink = False
