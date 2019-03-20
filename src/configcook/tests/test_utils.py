# -*- coding: utf-8 -*-
import os
import pytest


def test_to_bool():
    from configcook.utils import to_bool

    assert to_bool(True) is True
    assert to_bool("True") is True
    assert to_bool("true") is True
    assert to_bool("t") is True
    assert to_bool(False) is False
    assert to_bool("False") is False
    assert to_bool("false") is False
    assert to_bool("f") is False
    assert to_bool("yes") is True
    assert to_bool("y") is True
    assert to_bool("no") is False
    assert to_bool("n") is False
    assert to_bool("on") is True
    assert to_bool("off") is False
    with pytest.raises(ValueError):
        to_bool("o")
    assert to_bool("1") is True
    with pytest.raises(ValueError):
        to_bool("2")
    assert to_bool("0") is False
    with pytest.raises(ValueError):
        # must be text (or boolean)
        to_bool(1)


def test_to_list():
    from configcook.utils import to_list

    assert to_list("") == []
    assert to_list("hello") == ["hello"]
    assert to_list("hello world") == ["hello", "world"]
    assert to_list("there\nand back again") == ["there", "and", "back", "again"]


def test_to_lines():
    from configcook.utils import to_lines

    assert to_lines("") == []
    assert to_lines("hello") == ["hello"]
    assert to_lines("hello world") == ["hello world"]
    assert to_lines("there\nand back again") == ["there", "and back again"]


def test_to_path_parent():
    from configcook.utils import to_path

    assert to_path("") == os.getcwd()
    assert to_path(os.getcwd()) == os.getcwd()
    assert to_path(os.pardir) == os.path.realpath(os.path.join(os.getcwd(), os.pardir))


def test_to_path_home():
    from configcook.utils import to_path

    home = os.environ.get("HOME")
    if not home:
        # Cannot test this.
        return
    assert to_path("~") == home


def test_to_path_symlink(tmp_path):
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
