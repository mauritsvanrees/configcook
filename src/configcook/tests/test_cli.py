# -*- coding: utf-8 -*-
import pytest
import sys


def test_parse_options():
    from configcook.cli import parse_options

    orig_sys_argv = sys.argv.copy()
    try:
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
    finally:
        sys.argv = orig_sys_argv


def test_cli_main():
    from configcook.cli import main

    orig_sys_argv = sys.argv.copy()
    try:
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
    finally:
        sys.argv = orig_sys_argv
