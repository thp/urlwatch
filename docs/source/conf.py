# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

HERE = os.path.abspath(os.path.dirname(__file__) or '.')
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))


# -- Project information -----------------------------------------------------

project = 'urlwatch'
copyright = '2023 Thomas Perl'
author = 'Thomas Perl'

# The full version, including alpha/beta/rc tags
release = '2.28'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'inheritance_ascii_tree',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

master_doc = 'index'


# -- Options for man pages ---------------------------------------------------

man_pages = [
    ('manpage',       'urlwatch',            'Monitor webpages and command output for changes', '', '1'),
    ('configuration', 'urlwatch-config',     'Configuration of urlwatch behavior', '', '5'),
    ('jobs',          'urlwatch-jobs',       'Job types and configuration for urlwatch', '', '5'),
    ('filters',       'urlwatch-filters',    'Filtering output and diff data of urlwatch jobs', '', '5'),
    ('reporters',     'urlwatch-reporters',  'Reporters for change notifications', '', '5'),
    ('advanced',      'urlwatch-cookbook',   'Advanced topics and recipes for urlwatch', '', '7'),
    ('introduction',  'urlwatch-intro',      'Introduction to basic urlwatch usage', '', '7'),
    ('deprecated',    'urlwatch-deprecated', 'Documentation of feature deprecation in urlwatch', '', '7'),
]

man_show_urls = True
man_make_section_directory = True

# Distros/packagers can override this to point to their manpages web service
manpages_url = 'https://manpages.debian.org/{path}'
