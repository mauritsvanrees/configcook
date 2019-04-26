configcook: task automation by cooking recipes in a configuration file
======================================================================

configcook is a tool to automate tasks using a configuration file.
Think of Makefiles, but then with a configuration file using ``TOML`` syntax.
The tool is heavily inspired by the Buildout project.


Comparison with Buildout
------------------------

It aims to do the same as Buildout (the ``zc.buildout`` package).
Both have:

- extensions
- recipes
- extend configuration from other files

Big differences:

- Buildout installs packages itself.
  configcook calls ``pip`` on the command line.

- Buildout uses ``ConfigParser`` compatible ini-style configuration files.
  configcook uses TOML configuration files.

It would be great if extensions and recipes written for Buildout could work with configcook.
Currently this seems impossible without changes to those extensions and recipes.


``TOML`` configuration files
----------------------------

TOML is more expressive than ini-style configuration files.
In Buildout config you could write this::

    [buildout]
    a_string = 0
    a_number = 0
    a_list_of_strings = 0
    a_list_of_integers = 0

In ``TOML`` this would be::

    [configcook]
    a_string = "0"
    a_number = 0
    a_list_of_strings = ["0"]
    a_list_of_integers = [0]

So TOML is a bit more verbose, with quotes and brackets, but it avoids tedious parsing in recipes.
The tedious parsing is done by the `Python toml package <https://pypi.org/project/toml/>`_.
Note: the `pytoml package <https://pypi.org/project/pytoml/>`_ could be good too, but ``toml`` is more popular.

Also, compare how booleans are handled.
In buildout config it is completely up to the recipe to make sure that ``false`` means false,
instead of true because it is a non-empty string::

    [buildout]
    a_boolean_true = true
    # or maybe true/True/TRUE/yes/1/on
    a_boolean_false = false
    # or maybe false/False/FALSE/no/0/off

In configcook/TOML there is just one way::

    [configcook]
    a_boolean_true = true
    a_boolean_false = false

In Buildout you can append items with the ``+=`` construction when you extend files.
You need to be careful with multiple values::

    # original file:
    [buildout]
    single = one two
    multi =
        one
        two

    # file extending original file:
    [buildout]
    single += three
    multi +=
        three

    # result:
    [buildout]
    single =
        one two
        three
    multi =
        one
        two
        three

In configcook the above would give a parse error because ``parts +`` is not a valid key, so you must quote it.
It gives more consistency and flexibility though::

    # original file:
    [configcook]
    a_string = "1"
    a_number = 1
    a_list_of_strings = ["1"]
    a_list_of_integers = [1]

    # file extending original file:
    [configcook]
    "a_string+" = "2"
    "a_number+" = 2
    "a_list_of_strings+" = ["2"]
    "a_list_of_integers+' = [2]

    # result:
    [configcook]
    a_string = "12"
    a_number = 3
    a_list_of_strings = ["1", "2"]
    a_list_of_integers = [1, 2]

Technically, you can also add booleans this way, but it is not needed and not recommended.
If you do it:

- ``false + false`` is 0.
- ``false + true`` is 1.
- ``true + true`` is 2.

In Buildout you can remove items with the ``-=`` construction when you extend files:
Again, you need to be careful with multiple values::

    # original file:
    [buildout]
    single = one two
    multi =
        one
        two

    # file extending original file:
    [buildout]
    single -= one
    multi -=
        one

    # result:
    [buildout]
    single = one two
    multi =
        two


TODO: support ``-=`` for subtracting values.

Note: you can only add or subtract values that are of the same type.
For example, adding a string to a list will give a ``ConfigError``.

The above is the basic information you need about the ``TOML`` format and how configcook uses it.
See the `TOML specification <https://github.com/toml-lang/toml>`_ for more details.


``TOML`` and Python packages
----------------------------

``TOML`` was chosen by the Python community as format for specifying how to build a Python package.
A package author would do this in a ``pyproject.toml`` file.
See `PEP 518 <https://www.python.org/dev/peps/pep-0518/>`_, which includes an `overview of file formats considered <https://www.python.org/dev/peps/pep-0518/#overview-of-file-formats-considered>`_.

Within the ``pyproject.toml`` file, PEP 518 reserves a few names for tables (sections) that tools are expected to recognize and respect.
At the moment, these are:

- ``build-system``
- ``tool``

The PEP goes on to say: "Tables not specified in this PEP are reserved for future use by other PEPs."

So if you add configcook to your ``pyproject.toml`` file it should look something like this::

    [build-system]
    # Minimum requirements for the build system to execute.
    # PEP 508 specifications.
    requires = ["setuptools", "wheel", "configcook"]

    [tool.configcook]
    parts = tool.configcook.somepart

    [tool.configcook.somepart]
    recipe = some.recipe

If you need lots more configcook sections, it gets tedious to prepend all table names with ``tool.configcook``.
Also, configcook is definitely not only meant for Python packages.

TODO: so we want to make tool.configcook available under the configcook key as well.
And maybe tool.configcook.somepart under the somepart key.


Most important URLs
-------------------

- We are `on PyPI <https://pypi.org/project/configcook>`_, so you can do ``pip install configcook``.

- The code is at `github.com/mauritsvanrees/configcook  <https://github.com/mauritsvanrees/configcook>`_.
  I intend to either give other people write access there, or move it to an organisation.


Compatibility
-------------

``configcook`` aims to work on Python 2.7, Python 3.6, Python3.7 and PyPy2/3.
As long as you have a ``pip`` that still works on Python 2.7, it should work.


Design decisions
----------------

- We never directly install or uninstall Python packages.
  We use pip for that.
- We call pip on the command line.
  We might use some utility functions from pip in our Python code, but a package install or uninstall will always be done in a shell with pip.
- The packages end up wherever pip installs them.
  By default we expect this to be in a virtualenv, and will refuse to install anything if not.
  There will be options to go around this safety restriction, but then you should know what you are doing, as we might pollute your global Python install.
- We will not isolate packages.
  If you have one config section that installs development requirements and another for production requirements and you install them both, then you simply have both.
  Perhaps clever recipes could work around this limitation.
- pip is leading.
  You should be able to manually do ``pip install -r *requirements.txt -c *constraints.txt`` and have the same packages and versions installed as when you would have run configcook.
  configcook may install more, or suggest changes to those version files.
- Version pins are only in the requirements.txt and constraints.txt files, or variants like dev-requirements.txt.
- Extensions and recipes are encouraged to follow our design decisions, but we cannot enforce this.


Recipes
-------

Some hints for recipe authors who want their recipe to be a good citizen:

- A recipe class SHOULD inherit from ``configcook.recipes.BaseRecipe``.
- A recipe class ``__init__`` MUST accept a tuple of ``name, config, options``.  ``name`` is the name of the part or section.
- A recipe class SHOULD NOT change the ``config``.
  This is the parsed configcook configuration, in a dictionary of dictionaries.
- A recipe class MAY update its recipe ``options``.
  These are the parsed options in the section belonging to the recipe part.
- A recipe class SHOULD have a ``packages`` property that returns a list of packages to install.
  The list MAY be empty.
- A recipe class SHOULD have an ``install`` method.
