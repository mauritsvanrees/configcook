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


def test_parse_config():
    from configcook.config import ConfigCookConfig
    from configcook.config import parse_config

    orig_dir = os.getcwd()
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
        os.chdir(orig_dir)
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
