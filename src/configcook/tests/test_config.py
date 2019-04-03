# -*- coding: utf-8 -*-
import os
import pytest
import shutil
import tempfile


def test_ConfigCookConfig():
    from configcook.config import ConfigCookConfig

    # The basic structure is the same as a dict.
    assert ConfigCookConfig({}) == {}
    # But it is not the same object.
    assert ConfigCookConfig({}) is not {}
    # And we have a _raw attribute.
    assert ConfigCookConfig({})._raw == {}

    # Use slightly more interesting data.
    a_data = [1]
    orig = {"a": a_data}
    ccc = ConfigCookConfig(orig)
    assert ccc == orig
    assert ccc._raw == orig
    assert ccc._raw == ccc
    assert ccc is not orig
    assert ccc._raw is not orig
    assert ccc._raw is not ccc
    assert orig.get("a") == a_data
    assert ccc.get("a") == a_data
    assert ccc._raw.get("a") == a_data

    # Now change the original data.
    # This works the same as when you do new_dict = dict(old_dict):
    # changes in mutable keys (dict, list) get passed along,
    # but new values are really new.
    a_data.append(2)
    orig["b"] = 5
    assert ccc != orig
    assert ccc._raw != orig
    assert ccc._raw != ccc
    assert ccc is not orig
    assert ccc._raw is not orig
    assert ccc._raw is not ccc
    assert orig.get("a") == a_data
    assert ccc.get("a") == a_data
    assert ccc._raw.get("a") == [1]
    assert orig.get("b") == 5
    assert ccc.get("b") is None
    assert ccc._raw.get("b") is None

    # Now change the data in our class.
    ccc["a"].append(3)
    ccc["c"] = 42
    assert ccc != orig
    assert ccc._raw != orig
    assert ccc._raw != ccc
    assert ccc is not orig
    assert ccc._raw is not orig
    assert ccc._raw is not ccc
    assert orig.get("a") == a_data
    assert ccc.get("a") == a_data
    assert ccc._raw.get("a") == [1]
    assert orig.get("c") is None
    assert ccc.get("c") == 42
    assert ccc._raw.get("c") is None


def test_parse_config_paths(tmp_path, safe_working_dir):
    # tmp_path is a pathlib/pathlib2.Path object.
    from configcook.config import ConfigCookConfig
    from configcook.config import parse_config

    tempdir = tempfile.mkdtemp()
    try:
        file_path1 = os.path.join(tempdir, "file1.cfg")
        with open(file_path1, "w") as ccfile:
            ccfile.write("[configcook]\n")
            ccfile.write("a = 1")
        with pytest.raises(Exception):
            # This file is not in the current directory.
            # Gives FileNotFoundError on Py3, IOError on Py2.
            parse_config("file1.cfg")
        # absolute path
        assert parse_config(file_path1) == {"configcook": {"a": "1"}}
        assert isinstance(parse_config(file_path1), ConfigCookConfig)
        # in current dir
        os.chdir(tempdir)
        assert parse_config("file1.cfg") == {"configcook": {"a": "1"}}
        # relative path
        assert parse_config(
            os.path.join(os.pardir, os.path.basename(tempdir), "file1.cfg")
        ) == {"configcook": {"a": "1"}}
    finally:
        shutil.rmtree(tempdir)


def test_parse_config_home():
    from configcook.config import parse_config

    # make temporary file in home dir
    fd, filepath = tempfile.mkstemp(dir=os.path.expanduser("~"))
    try:
        with open(fd, "w") as ccfile:
            ccfile.write("[configcook]\n")
            ccfile.write("a = 1")
        # user should be expanded
        assert parse_config(os.path.join("~", os.path.basename(filepath))) == {
            "configcook": {"a": "1"}
        }
    finally:
        os.remove(filepath)


def test_parse_config_extends():
    from configcook.config import parse_config

    tempdir = tempfile.mkdtemp()
    try:
        file_path1 = os.path.join(tempdir, "file1.cfg")
        # file 1 extends file 2
        with open(file_path1, "w") as ccfile:
            ccfile.write("[configcook]\nextends = file2.cfg\na = 1")
        file_path2 = os.path.join(tempdir, "file2.cfg")
        with open(file_path2, "w") as ccfile:
            ccfile.write("[configcook]\nb = 2")
        assert parse_config(file_path1) == {
            "configcook": {"a": "1", "b": "2", "extends": ["file2.cfg"]}
        }
        # file 3 extends file 1
        file_path3 = os.path.join(tempdir, "file3.cfg")
        with open(file_path3, "w") as ccfile:
            ccfile.write("[configcook]\nextends = file1.cfg\nc = 3")
        assert parse_config(file_path3) == {
            "configcook": {
                "a": "1",
                "b": "2",
                "c": "3",
                "extends": ["file1.cfg", "file2.cfg"],
            }
        }
        # file 5 extends file 3 and 4
        file_path4 = os.path.join(tempdir, "file4.cfg")
        with open(file_path4, "w") as ccfile:
            ccfile.write("[configcook]\nd = 4")
        file_path5 = os.path.join(tempdir, "file5.cfg")
        with open(file_path5, "w") as ccfile:
            ccfile.write("[configcook]\nextends = file3.cfg file4.cfg\ne = 5")
        assert parse_config(file_path5) == {
            "configcook": {
                "a": "1",
                "b": "2",
                "c": "3",
                "d": "4",
                "e": "5",
                "extends": ["file3.cfg", "file1.cfg", "file2.cfg", "file4.cfg"],
            }
        }
    finally:
        shutil.rmtree(tempdir)


def test_parse_config_plus():
    from configcook.config import parse_config

    tempdir = tempfile.mkdtemp()
    try:
        file_path1 = os.path.join(tempdir, "file1.cfg")
        # file 1 extends file 2
        with open(file_path1, "w") as ccfile:
            ccfile.write("[configcook]\nextends = file2.cfg\na = 1")
        # file 2 adds to a value of file 1
        file_path2 = os.path.join(tempdir, "file2.cfg")
        with open(file_path2, "w") as ccfile:
            ccfile.write("[configcook]\na += 2")
        assert parse_config(file_path1) == {
            "configcook": {"a": "1\n2", "extends": ["file2.cfg"]}
        }
    finally:
        shutil.rmtree(tempdir)


def test_merge_dicts():
    from configcook.config import _merge_dicts as md

    # We do not make inline changes: the result is a new dict.
    a = {}
    b = {}
    assert md(a, b) == {}
    assert md(a, b) is not a
    assert md(a, b) is not b
    # The value of the second dict wins:
    assert md({"a": "1"}, {"b": "2"}) == {"a": "1", "b": "2"}
    assert md({"a": "1"}, {"a": "2"}) == {"a": "2"}
    # Nested dictionaries are handled.
    assert md({"a": {"a": "1"}}, {"b": {"b": "2"}}) == {
        "a": {"a": "1"},
        "b": {"b": "2"},
    }
    assert md({"a": {"a": "1"}}, {"a": {"b": "2"}}) == {"a": {"a": "1", "b": "2"}}
    assert md({"a": {"a": "1"}}, {"a": {"a": "2"}}) == {"a": {"a": "2"}}
    # Nested lists are handled.
    assert md({"a": {"a": ["1"]}}, {"b": {"b": ["2"]}}) == {
        "a": {"a": ["1"]},
        "b": {"b": ["2"]},
    }
    assert md({"a": {"a": ["1"]}}, {"a": {"b": ["2"]}}) == {
        "a": {"a": ["1"], "b": ["2"]}
    }
    assert md({"a": {"a": ["1"]}}, {"a": {"a": ["2"]}}) == {"a": {"a": ["2"]}}
    # We can add to a value with +=.
    assert md({"a": "1"}, {"a +": "2"}) == {"a": "1\n2"}
    assert md({"a": "1"}, {"a+": "2"}) == {"a": "1\n2"}
    assert md({"a": "1"}, {"a       +": "2"}) == {"a": "1\n2"}
    assert md({"a": "a b"}, {"a +": "c\nd"}) == {"a": "a b\nc\nd"}
    assert md({"a": "a\nb"}, {"a +": "c d"}) == {"a": "a\nb\nc d"}
