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
        with pytest.raises(SystemExit):
            # Gives FileNotFoundError on Py3, IOError on Py2.
            # But this is caught in main.
            sys.argv = "bin/configcook -c none.cfg".split()
            main()
        # TODO: check with "configcook": should find the full script path
        # with shutil.which.
    finally:
        sys.argv = orig_sys_argv
