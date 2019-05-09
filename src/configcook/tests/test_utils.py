# -*- coding: utf-8 -*-
from subprocess import CalledProcessError

import os
import pytest


def test_to_path_parent():
    from configcook.utils import to_path

    assert to_path("") == os.getcwd()
    assert to_path(os.getcwd()) == os.getcwd()
    assert to_path(os.pardir) == os.path.realpath(os.path.join(os.getcwd(), os.pardir))
    with pytest.raises(ValueError):
        # must be text
        to_path([])


def test_to_path_home():
    from configcook.utils import to_path

    home = os.environ.get("HOME")
    assert to_path("~") == home


def test_to_path_symlink(tmp_path, safe_working_dir):
    # tmp_path is a pathlib/pathlib2.Path object.
    from configcook.utils import to_path

    str_path = str(tmp_path)
    os.chdir(str_path)
    assert to_path("") == str_path
    source_path = os.path.join(str_path, "source")
    with open(source_path, "w") as source:
        source.write("hello")
    # Let destination point to the source.
    os.symlink("source", "destination")
    assert to_path("source") == source_path
    assert to_path("destination") == source_path


def test_format_command_for_print():
    from configcook.utils import format_command_for_print as fp

    assert fp([]) == ""
    assert fp(["foo"]) == "foo"
    assert fp(["foo", "bar baz"]) == "foo 'bar baz'"
    with pytest.raises(ValueError):
        # must be a list
        fp("")


def test_call_or_fail():
    from configcook.utils import call_or_fail

    assert call_or_fail(["echo"]) == 0
    with pytest.raises(CalledProcessError) as exc:
        call_or_fail(["ln"])
    assert exc.value.returncode == 1


def test_call_with_exitcode():
    from configcook.utils import call_with_exitcode

    assert call_with_exitcode(["echo", "foo"]) == 0
    assert call_with_exitcode(["ln"]) == 1


def test_call_with_output_or_fail():
    from configcook.utils import call_with_output_or_fail

    assert call_with_output_or_fail(["echo", "foo"]) == b"foo\n"
    with pytest.raises(CalledProcessError) as exc:
        call_with_output_or_fail(["ln"])
    assert exc.value.returncode == 1
