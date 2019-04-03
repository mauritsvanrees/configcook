# -*- coding: utf-8 -*-
from textwrap import dedent
import os
import pytest
import sys


def test_parse_options(safe_sys_argv):
    from configcook.cli import parse_options

    # defaults
    sys.argv = ["configcook"]
    options = parse_options()
    assert options.configfile == "cc.cfg"
    assert not options.debug
    assert not options.verbose
    # -c / --config
    sys.argv = "configcook -c second.cfg".split()
    options = parse_options()
    assert options.configfile == "second.cfg"
    sys.argv = "configcook --config third.cfg".split()
    # -D / --debug
    sys.argv = "configcook -D".split()
    options = parse_options()
    assert options.debug
    sys.argv = "configcook --debug".split()
    options = parse_options()
    assert options.debug
    # -v / --verbose
    sys.argv = "configcook -v".split()
    options = parse_options()
    assert options.verbose
    sys.argv = "configcook --verbose".split()
    options = parse_options()
    assert options.verbose


def test_cli_main_without_config_file(safe_sys_argv):
    from configcook.cli import main

    sys.argv = "bin/configcook -c none.cfg".split()
    with pytest.raises(SystemExit) as exc:
        # Gives FileNotFoundError on Py3, IOError on Py2.
        # But this is caught in main.
        main()
    assert exc.value.code == 1
    # Same with verbose.
    sys.argv = "bin/configcook -v -c none.cfg".split()
    with pytest.raises(SystemExit) as exc:
        # Gives FileNotFoundError on Py3, IOError on Py2.
        # But this is caught in main.
        main()
    assert exc.value.code == 1
    # Maybe try only "configcook": should find the full script path
    # with shutil.which.  Or actually: probably better to only support
    # bin/configcook, because of our virtualenv requirement.
    # Ah: when called with "configcook" as command line,
    # sys.argv[0] is still the absolute path.
    sys.argv = "bin/configcook --help".split()
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_cli_main_no_packages(tmp_path, safe_sys_argv, safe_working_dir):
    # tmp_path is a pathlib/pathlib2.Path object.
    from configcook.cli import main

    contents = dedent(
        """
[configcook]
extensions = configcook:extension_example
parts = test

[test]
recipe = configcook:command
command = echo Hello
"""
    )
    str_path = str(tmp_path)
    os.chdir(str_path)
    config_file = os.path.join(str_path, "a.cfg")
    with open(config_file, "w") as cf:
        cf.write(contents)
    sys.argv = "configcook -c a.cfg".split()
    with pytest.raises(SystemExit) as exc:
        # This fails because we are not in a virtualenv.
        main()
    assert exc.value.code == 1
    # We have an extra options that does not install packages,
    # so we skip the virtualenv check.
    sys.argv = "configcook --no-packages -c a.cfg".split()
    main()
    # I would like to pass 'capsys' from pytest to the test function,
    # and capture and test the output, but it does not work.
    # Maybe because I am using PyPy3?
    # captured = capsys.readouterr()
    # captured.out == 'foo'
