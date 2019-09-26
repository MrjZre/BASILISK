# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import sphinx_rtd_theme

# sys.path.insert(0, os.path.abspath('.'))
#sys.path.append("/Users/johnmartin/Documents/Graduate School/BasiliskTutorial/BSK_Sphinx/source/utilities/MonteCarlo")
sys.path.append("~/Library/Python/3.7/lib/python/site-packages/breathe/")
sys.path.append("~/Basilisk/src/fswAlgorithms/*")


# -- Project information -----------------------------------------------------

project = u'Basilisk'
copyright = u'2019, AVS Lab'
author = u'AVS Lab'

# The short X.Y version
version = u''
# The full version, including alpha/beta/rc tags
release = u'0.0.1'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    "sphinx_rtd_theme",
    'recommonmark',
    'breathe',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'canonical_url': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': 'white',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': True
}
# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Basiliskdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'Basilisk.tex', u'Basilisk Documentation',
     u'AVS Lab', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'basilisk', u'Basilisk Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Basilisk', u'Basilisk Documentation',
     author, 'Basilisk', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------


breathe_projects = {"Basilisk": "~/Basilisk/src/*"}

from glob import glob
import shutil

def writeTOC(name):
    if "/" in name:
        name = os.path.basename(os.path.normpath(name))
    lines = name + "\n" + "="*len(name) + "\n\n"
    # lines += """.. toctree::\n   :maxdepth: 1\n   :caption: """ + name + ":\n\n"
    lines += """.. toctree::\n   :maxdepth: 1\n   :caption: """ + "Directories" + ":\n\n"

    return lines

def writeIndex(name):
    lines = "   " + name + "/index\n"
    return lines

def writeFolder(name):
    if "/" in name:
        name = os.path.basename(os.path.normpath(name))
    lines = "   " + name + "\n"

    return lines

def autoDoc(path, files):
    if "/" in path:
        name = os.path.basename(path)
    fileNames = []
    for file in files:
        fileName = file[file.rfind("/"):][1:]
        fileNames.append(fileName)
    sources = {name : (path, fileNames)}
    lines = """.. autodoxygenindex::\n   :project: """ + name + """\n\n"""
    return lines, sources


def configureDir(docDir, srcDir):
    # Find all files and directories in the src directory
    sub_dirs = glob(srcDir + '*/')
    removeList = []
    for i in range(len(sub_dirs)):
        if "_Documentation" in sub_dirs[i] or "_UnitTest" in sub_dirs[i] or "__pycache__" in sub_dirs[i]:
            removeList.extend([i])
    for i in sorted(removeList, reverse=True):
        del sub_dirs[i]



    docDir = docDir
    docDirName = docDir[:-1]

    srcDir = srcDir
    srcDirName = srcDir[:-1]

    # Create the Documentation Folder
    if os.path.isdir(docDir):
        shutil.rmtree(docDir)
    os.mkdir(docDir)

    with open(docDir + "index.rst", "w") as f:
        f.write(writeTOC(docDirName))
        if sub_dirs == []:
            f.write(writeFolder(docDirName))

    for dir in sub_dirs:
        dirName = dir[dir[:dir.rfind("/")].rfind("/"):][1:-1]  # For ex 'fswAlgorithms'
        doc_dir_path = docDir + dirName  # i.e. /Documentation/fswAlgorithms
        src_dir_path = srcDir + dirName

        files = glob(src_dir_path + "/*.c")
        files.extend(glob(src_dir_path + "/*.h"))
        files.extend(glob(src_dir_path + "/*.cpp"))
        files.extend(glob(src_dir_path + "/*.py"))


        with open(docDir + "index.rst", "a+") as f:
            dirName = dir[dir[:dir.rfind("/")].rfind("/"):][1:-1]  # For ex 'fswAlgorithms'
            f.write(writeIndex(dirName))

        # Create Folder
        if not os.path.isdir(doc_dir_path):
            os.mkdir(doc_dir_path)
            configureDir(doc_dir_path + "/", src_dir_path + "/")

        # Create the doc_directory .rst file which contains the auto-documented code
        sources = {}
        if not files == []:
            with open(doc_dir_path+"/"+dirName+".rst", "w") as f:
                f.write(writeTOC(dirName))
                lines, sources = autoDoc(src_dir_path, files)
                f.write(lines)
        breathe_projects_source.update(sources)

breathe_projects_source = {}
configureDir("Documentation/", "../../../Basilisk/src/")

# breathe_projects_source = {"BasiliskFSW": ("../../src/fswAlgorithms/attControl/MRP_Feedback", ['MRP_Feedback.c', 'MRP_Feedback.h'])}

