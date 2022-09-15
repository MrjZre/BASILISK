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
import numpy as np
import sphinx_rtd_theme
import datetime


# -- Project information -----------------------------------------------------

now = datetime.datetime.now()
f = open('bskVersion.txt', 'r')
bskVersion = f.read()
f.close()

project = u'Basilisk'
copyright = str(now.year) + u', Autonomous Vehicle Systems (AVS) Laboratory'
author = u'AVS Lab'
release = bskVersion
version = u'version ' + release


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
    'sphinx.ext.napoleon',
    # 'sphinx.ext.inheritance_diagram',
    "sphinx_rtd_theme",
    'recommonmark',
    'breathe'
]

# Add any paths that contain templates here, relative to this directory.
#templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
#source_suffix = ['.rst', '.md', '.svg']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

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
html_theme_options = {
    'style_nav_header_background': '#CFB87C'
}

html_context = {
    'css_files': ['_static/css/custom.css']
}

html_logo = "./_images/static/Basilisk-Logo.png"
#
# html_theme_options = {
#     'canonical_url': '',
#     'logo_only': False,
#     'display_version': True,
#     'prev_next_buttons_location': 'bottom',
#     'style_external_links': False,
#     'vcs_pageview_mode': '',
#     'style_nav_header_background': 'white',
#     # Toc options
#     'collapse_navigation': True,
#     'sticky_navigation': True,
#     'navigation_depth': 4,
#     'includehidden': True,
#     'titles_only': True
# }
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


# breathe_projects = {"Basilisk": "../../src/*"}

from glob import glob
import shutil

class fileCrawler():
    def __init__(self, newFiles=False):
        self.newFiles = newFiles
        self.breathe_projects_source = {}
        self.counter = 0

    def grabRelevantFiles(self,dir_path):
        dirs_in_dir = glob(dir_path + '*/')
        files_in_dir = glob(dir_path + "*.h")
        files_in_dir.extend(glob(dir_path + "*.c"))
        files_in_dir.extend(glob(dir_path + "*.cpp"))
        files_in_dir.extend(glob(dir_path + "*.py"))


        # Remove any directories that shouldn't be added directly to the website
        removeList = []
        for i in range(len(dirs_in_dir)):
            if "_Documentation" in dirs_in_dir[i] or \
                    "__pycache__" in dirs_in_dir[i] or \
                    "_VizFiles" in dirs_in_dir[i] or \
                    "Support" in dirs_in_dir[i] or \
                    "cmake" in dirs_in_dir[i] or \
                    "topLevelModules" in dirs_in_dir[i] or \
                    "outputFiles" in dirs_in_dir[i] or \
                    "msgAutoSource" in dirs_in_dir[i] or \
                    "alg_contain" in dirs_in_dir[i] or \
                    "dataForExamples" in dirs_in_dir[i] or \
                    "tests" in dirs_in_dir[i]:
                removeList.extend([i])
        for i in sorted(removeList, reverse=True):
            del dirs_in_dir[i]

        # Remove unnecessary source files (all files except .py, .c, .cpp, .h)
        removeList = []
        for i in range(len(files_in_dir)):
            if "__init__" in files_in_dir[i] or \
                    "conftest.py" in files_in_dir[i] or \
                    "*.xml" in files_in_dir[i] or \
                    "vizMessage.pb.cc" in files_in_dir[i] or \
                    "vizMessage.pb.h" in files_in_dir[i] or \
                    "vizMessage.proto" in files_in_dir[i] or \
                    "EGM9615.h" in files_in_dir[i] or \
                    "SunLineKF_test_utilities.py" in files_in_dir[i] or \
                    "datashader_utilities.py" in files_in_dir[i] or \
                    "reportconf.py" in files_in_dir[i]:
                removeList.extend([i])
        for i in sorted(removeList, reverse=True):
            del files_in_dir[i]

        paths_in_dir = []
        paths_in_dir.extend(dirs_in_dir)
        paths_in_dir.extend(files_in_dir)

        return paths_in_dir

    def seperateFilesAndDirs(self,paths):
        files = []
        dirs = []
        for path in paths:
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                dirs.append(path)
        return sorted(files), sorted(dirs)

    def populateDocIndex(self, index_path, file_paths, dir_paths):

        # get the folder name
        name = os.path.basename(os.path.normpath(index_path))
        lines = ""

        # if a _default.rst file exists in a folder, then use it to generate the index.rst file
        try:
            pathToFolder, folderName = dir_paths[0].split(name)
            docFileName = os.path.join(os.path.join(pathToFolder, name),  '_default.rst')
            with open(docFileName, 'r') as docFile:
                docContents = docFile.read()
            lines += docContents + "\n\n"

        except: # Auto-generate the index.rst file
            # add page tag
            if name.startswith("_"):
                pathToFolder = index_path.split("/"+name)[0]
                lines += ".. " + name + pathToFolder.split("/")[-1] + ":\n\n"
            elif name == 'utilities':
                pathToFolder = index_path.split("/" + name)[0]
                lines += ".. _Folder_" + name + pathToFolder.split("/")[-1] + ":\n\n"
            else:
                lines += ".. _Folder_" + name + ":\n\n"

            # Title the page
            lines += name + "\n" + "=" * len(name) + "\n\n"

            # pull in folder _doc.rst file if it exists
            try:
                pathToFolder, folderName = dir_paths[0].split(name)
                docFileName = os.path.join(os.path.join(pathToFolder, name), '_doc.rst')
                if os.path.isfile(docFileName):
                    with open(docFileName, 'r') as docFile:
                        docContents = docFile.read()
                    lines += docContents + "\n\n"
            except:
                pass

            # Add a linking point to all local files
            lines += """\n\n.. toctree::\n   :maxdepth: 1\n   :caption: """ + "Files:\n\n"
            calledNames = []
            for file_path in sorted(file_paths):
                fileName = os.path.basename(os.path.normpath(file_path))
                fileName = fileName[:fileName.rfind('.')]
                if not fileName in calledNames:
                    lines += "   " + fileName + "\n"
                    calledNames.append(fileName)

            # Add a linking point to all local directories
            lines += """.. toctree::\n   :maxdepth: 1\n   :caption: """ + "Directories:\n\n"
            for dir_path in sorted(dir_paths):
                dirName = os.path.basename(os.path.normpath(dir_path))
                lines += "   " + dirName + "/index\n"

        if self.newFiles:
            with open(os.path.join(index_path, "index.rst"), "w") as f:
                f.write(lines)

    def generateAutoDoc(self, path, files_paths):
        if "/" in path:
            name = os.path.basename(path)
        sources = {}

        # Sort the files by language
        py_file_paths = sorted([s for s in files_paths if ".py" in s])
        c_file_paths = sorted([s for s in files_paths if ".c" in s or ".cpp" in s or ".h" in s])

        # Create the .rst file for C-Modules

        # Identify .h file and .c/.cpp that share the same basename
        c_file_basenames = []
        c_file_local_paths = []
        for c_file_path in c_file_paths:
            c_file_name = os.path.basename(c_file_path)
            c_file_local_paths.append(c_file_name)
            c_file_name = c_file_name[:c_file_name.rfind('.')]
            c_file_basenames.append(c_file_name)

        c_file_basenames = np.unique(c_file_basenames)

        lines = ""
        lines += ".. _" + name + ":\n\n"
        lines += name + "\n" + "=" * len(name) + "\n\n"
        lines += """.. toctree::\n   :maxdepth: 1\n   :caption: """ + name + ":\n\n"

        if not c_file_paths == []:
            # Identify where the module lives relative to source
            src_path = os.path.dirname(c_file_path)
            module_files = []
            sources = {}
            for c_file_basename in c_file_basenames:

                module_files_temp = []
                lines = ""
                if c_file_basename == 'orbitalMotion' or c_file_basename == 'rigidBodyKinematics':
                    pathToFolder = src_path.split("/" + c_file_basename)[0]
                    lines += ".. _" + c_file_basename + pathToFolder.split("/")[-1] + ":\n\n"
                else:
                    lines += ".. _" + c_file_basename + ":\n\n"
                if "fswMessages" in src_path \
                        or "simFswInterfaceMessages" in src_path \
                        or "simMessages" in src_path\
                        or "architecture" in src_path\
                        or "utilities" in src_path:
                    lines += c_file_basename + "\n" + "=" * (len(c_file_basename) + 8) + "\n\n"
                else:
                    lines += "Module: " + c_file_basename + "\n" + "=" * (len(c_file_basename) + 8) + "\n\n"

                # pull in the module documentation file if it exists
                docFileName = os.path.join(src_path, c_file_basename + '.rst')
                if os.path.isfile(docFileName):
                    with open(docFileName, 'r', encoding="utf8") as docFile:
                        docContents = docFile.read()
                    lines += docContents + "\n\n"
                    lines += "----\n\n"

                # Link the path with the modules for Breathe
                module_files.extend([s for s in c_file_local_paths if c_file_basename in s])
                module_files_temp.extend([s for s in c_file_local_paths if c_file_basename in s])

                # Populate the module's .rst
                for module_file in module_files_temp:
                    if ".h" in module_file:
                        if name == "_GeneralModuleFiles":
                            name += str(self.counter)
                            self.counter += 1
                        lines += """.. autodoxygenfile:: """ + module_file + """\n   :project: """ + name + """\n\n"""
                        # lines += """.. inheritance-diagram:: """ + module_file + """\n\n"""

                if self.newFiles:
                    with open(os.path.join(path,  c_file_basename + ".rst"), "w") as f:
                        f.write(lines)

            sources.update({name: (src_path, module_files)})

        # Create the .rst file for the python module
        if not py_file_paths == []:
            # Add the module path to sys.path so sphinx can produce docs
            src_dir = path[path.find("/")+1:]
            src_dir = src_dir[src_dir.find("/")+1:]
            sys.path.append(os.path.abspath(officialSrc+"/"+src_dir))

        for py_file in sorted(py_file_paths):
            fileName = os.path.basename(py_file)
            if fileName not in ["__init__.py"]:
                fileName = fileName[:fileName.rfind('.')]
                lines = ".. _"+ fileName + ":\n\n"
                lines += fileName + "\n" + "=" * len(fileName) + "\n\n"
                lines += """.. toctree::\n   :maxdepth: 1\n   :caption: """ + "Files" + ":\n\n"
                lines += """.. automodule:: """ + fileName + """\n   :members:\n   :show-inheritance:\n\n"""
                if self.newFiles:
                    with open(path+"/"+fileName+".rst", "w") as f:
                        f.write(lines)

        return sources




    def run(self, srcDir):
        # Find all files and directories in the src directory
        paths_in_dir = self.grabRelevantFiles(srcDir)

        # In the local folder, divvy up files and directories
        file_paths, dir_paths = self.seperateFilesAndDirs(paths_in_dir)

        index_path = os.path.relpath(srcDir, officialSrc)
        if index_path == ".":
            index_path = "/"

        try:
            os.makedirs(officialDoc + index_path)
        except:
            pass

        # Populate the index.rst file of the local directory
        self.populateDocIndex(officialDoc+"/"+index_path, file_paths, dir_paths)

        # Generate the correct auto-doc function for C, C++, and python modules
        sources = self.generateAutoDoc(officialDoc+"/"+index_path, file_paths)

        # Need to update the translation layer from doxygen to sphinx (breathe)
        self.breathe_projects_source.update(sources)

        # Recursively go through all directories in source, documenting what is available.
        for dir_path in sorted(dir_paths):
            self.run(dir_path)

        if self.newFiles:
            return self.breathe_projects_source
        else:
            return

rebuild = True
officialSrc = "../../src"
officialDoc = "./Documentation/"

fileCrawler = fileCrawler(rebuild)
import pickle

if rebuild:
    if os.path.exists(officialDoc):
        shutil.rmtree(officialDoc)
    # adjust the fileCrawler path to a local folder to just build a sub-system
    breathe_projects_source = fileCrawler.run(officialSrc)
    # breathe_projects_source = fileCrawler.run(officialSrc+"/fswAlgorithms/fswMessages")
    # breathe_projects_source = fileCrawler.run(officialSrc+"/fswAlgorithms")
    # breathe_projects_source = fileCrawler.run(officialSrc+"/simulation/environment")
    # breathe_projects_source = fileCrawler.run(officialSrc+"/moduleTemplates")
    # breathe_projects_source = fileCrawler.run(officialSrc+"/simulation/vizard")
    # breathe_projects_source = fileCrawler.run(officialSrc+"/architecture")
    breathe_projects_source = fileCrawler.run("../../examples")
    breathe_projects_source = fileCrawler.run("../../externalTools")
    with open("breathe.data", 'wb') as f:
        pickle.dump(breathe_projects_source, f)
else:
    with open('breathe.data', 'rb') as f:
        breathe_projects_source = pickle.load(f)
    #breathe_projects_source = pickle.load('breathe.data')
    #fileCrawler.run("../../../Basilisk/src/")

#TODO: Pickle the breathe_project_source and load that back in

# Example of how to link C with Breathe
# breathe_projects_source = {"BasiliskFSW": ("../../src/fswAlgorithms/attControl/mrpFeedback", ['mrpFeedback.c', 'mrpFeedback.h'])}

