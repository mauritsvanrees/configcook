configcook: task automation by cooking recipes in a configuration file
======================================================================

configcook is a tool to automate tasks using a configuration file.
Think of Makefiles, but then with a configuration file using Python ConfigParser syntax.
The tool is heavily inspired by the Buildout project.


Comparison with Buildout
------------------------

It aims to do the same as Buildout (the ``zc.buildout`` package), but without directly installing Python packages.
configcook calls ``pip`` on the command line when it wants to install a package.
Both have:

- extensions
- recipes
- ConfigParser compatible config (possibly with small additions)

It would be great if extensions and recipes written for Buildout could work with configcook.
Currently this seems impossible without changes to those extensions and recipes.

The aim is to not need changes to a buildout recipe section, and ideally not to any part of ``buildout.cfg``.
But don't count on this.


Most important URLs
-------------------

- We are `on PyPI <https://pypi.org/project/configcook>`_, so you can do ``pip install configcook``.

- The code is at `github.com/mauritsvanrees/configcook  <https://github.com/mauritsvanrees/configcook>`_.


Compatibility
-------------

``configcook`` aims to work on Python 2.7, Python 3.6, Python3.7 and PyPy2/3.
As long as you have a ``pip`` that still works on Python 2.7, it should work.


Design decisions
----------------

* We never directly install or uninstall Python packages. We use pip for that.
* We call pip on the command line. We might use some utility functions from pip in our Python code, but a package install or uninstall will always be done in a shell with pip.
* The packages end up wherever pip installs them. By default we expect this to be in a virtualenv, and will refuse to install anything if not. There will be options to go around this safety restriction, but then you should know what you are doing, as we might pollute your global Python install.
* We will not isolate packages. If you have one config section that installs development requirements and another for production requirements and you install them both, then you simply have both.  Perhaps clever recipes could work around this limitation.
* pip is leading. You should be able to manually do ``pip install -r *requirements.txt -c *constraints.txt`` and have the same packages and versions installed as when you would have run configcook.  configcook may install more, or suggest changes to those version files.
* Version pins are only in the requirements.txt and constraints.txt files, or variants like dev-requirements.txt.
* Extensions and recipes are encouraged to follow our design decisions, but we cannot enforce this.


Recipes
-------

Some hints for recipe authors who want their recipe to be a good citizen:

- A recipe class SHOULD inherit from ``configcook.recipes.BaseRecipe``.
- A recipe class ``__init__`` MUST accept a tuple of ``name, config, options``.  ``name`` is the name of the part or section.
- A recipe class SHOULD NOT change the ``config``.  This is the parsed configcook configuration, in a dictionary of dictionaries.
- A recipe class MAY update its recipe ``options``.  These are the parsed options in the section belonging to the recipe part.
- A recipe class SHOULD have a ``packages`` property that returns a list of packages to install.  The list MAY be empty.
- A recipe class SHOULD have an ``install`` method.
