# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime
import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

project = "TerraVisu"
copyright = f"2017 - {datetime.datetime.now().year}, Autonomens"
author = "Autonomens"
release = open(os.path.join(root, "project", "VERSION")).read()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.todo",
    "sphinx_immaterial"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

exclude_patterns = ['_build']
pygments_style = 'sphinx'

html_theme = "sphinx_immaterial"
html_favicon = "_static/favicon.ico"
html_static_path = ["_static"]
html_logo = "_static/logo.png"

# Material theme options (see theme.conf for more information)
html_theme_options = {
    "icon": {
        "repo": "fontawesome/brands/github",
        "edit": "material/file-edit-outline",
    },
    "site_url": "https://demo-terravisu-territoires.makina-corpus.com/",
    "repo_url": "https://github.com/Terralego/TerraVisu/",
    "repo_name": "TerraVisu",
    "edit_uri": "blob/main/docs",
    "globaltoc_collapse": True,
    "features": [
        "navigation.expand",
        # "navigation.tabs",
        # "toc.integrate",
        "navigation.sections",
        # "navigation.instant",
        # "header.autohide",
        "navigation.top",
        # "navigation.tracking",
        # "search.highlight",
        "search.share",
        "toc.follow",
        "toc.sticky",
        "content.tabs.link",
        "announce.dismiss",
    ],
    "palette": [
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "blue",
            "accent": "light-blue",
            "toggle": {
                "icon": "material/weather-night",
                "name": "Switch to dark mode",
            },
        },
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "red",
            "accent": "deep-orange",
            "toggle": {
                "icon": "material/weather-sunny",
                "name": "Switch to light mode",
            },
        },
    ],
    "social": [
        {
            "icon": "fontawesome/brands/github",
            "link": "https://github.com/Terralego/TerraVisu/"
        },
        {
            "icon": "fontawesome/brands/linkedin",
            "link": "https://www.linkedin.com/company/makina-corpus",
        },
    ],
    "toc_title_is_page_title": True,
}

# Output file base name for HTML help builder.
htmlhelp_basename = 'TerraVisudoc'

latex_documents = [
    ('index', 'TerraVisu.tex', 'TerraVisu Documentation',
     'Makina Corpus Territoires', 'manual'),
]

man_pages = [
    ('index', 'terravisu', 'TerraVisu Documentation',
     ['Makina Corpus Territoires'], 1)
]
html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}
texinfo_documents = [
    ('index', 'TerraVisu', 'TerraVisu Documentation',
     'Makina Corpus Territoires', 'TerraVisu', 'One line description of project.',
     'Miscellaneous'),
]
