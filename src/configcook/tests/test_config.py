# -*- coding: utf-8 -*-
import os
import pytest
import tempfile


def test_ConfigCookConfig_is_dict_like():
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


def test_ConfigCookConfig_substitute():
    from configcook.config import ConfigCookConfig

    conf = {"A": {"a": "${:b}", "b": "value of b"}}
    cooked = ConfigCookConfig(conf)
    cooked.substitute_all()
    assert cooked == {"A": {"a": "value of b", "b": "value of b"}}


def test_parse_toml_config_paths(tmp_path, safe_working_dir):
    # tmp_path is a pathlib/pathlib2.Path object.
    from configcook.config import ConfigCookConfig
    from configcook.config import parse_toml_config

    tempdir = str(tmp_path)
    file_path1 = os.path.join(tempdir, "file1.toml")
    with open(file_path1, "w") as ccfile:
        ccfile.write("[configcook]\n")
        ccfile.write("a = 1")
    with pytest.raises(Exception):
        # This file is not in the current directory.
        # Gives FileNotFoundError on Py3, IOError on Py2.
        parse_toml_config("file1.toml")
    # absolute path
    assert parse_toml_config(file_path1) == {"configcook": {"a": 1}}
    assert isinstance(parse_toml_config(file_path1), ConfigCookConfig)
    # in current dir
    os.chdir(tempdir)
    assert parse_toml_config("file1.toml") == {"configcook": {"a": 1}}
    # relative path
    assert parse_toml_config(
        os.path.join(os.pardir, os.path.basename(tempdir), "file1.toml")
    ) == {"configcook": {"a": 1}}


def test_parse_toml_config_home():
    from configcook.config import parse_toml_config

    # make temporary file in home dir
    fd, filepath = tempfile.mkstemp(dir=os.path.expanduser("~"))
    try:
        with open(fd, "w") as ccfile:
            ccfile.write("[configcook]\n")
            ccfile.write("a = 1")
        # user should be expanded
        assert parse_toml_config(os.path.join("~", os.path.basename(filepath))) == {
            "configcook": {"a": 1}
        }
    finally:
        os.remove(filepath)


def test_parse_toml_config_extends(tmp_path):
    from configcook.config import parse_toml_config

    tempdir = str(tmp_path)
    file_path1 = os.path.join(tempdir, "file1.toml")
    # file 1 extends file 2
    with open(file_path1, "w") as ccfile:
        ccfile.write("[configcook]\nextends = ['file2.toml']\na = 1")
    file_path2 = os.path.join(tempdir, "file2.toml")
    with open(file_path2, "w") as ccfile:
        ccfile.write("[configcook]\nb = 2")
    assert parse_toml_config(file_path1) == {
        "configcook": {"a": 1, "b": 2, "extends": ["file2.toml"]}
    }
    # file 3 extends file 1
    file_path3 = os.path.join(tempdir, "file3.toml")
    with open(file_path3, "w") as ccfile:
        ccfile.write('[configcook]\nextends = ["file1.toml"]\nc = 3')
    assert parse_toml_config(file_path3) == {
        "configcook": {"a": 1, "b": 2, "c": 3, "extends": ["file1.toml", "file2.toml"]}
    }
    # file 5 extends file 3 and 4
    file_path4 = os.path.join(tempdir, "file4.toml")
    with open(file_path4, "w") as ccfile:
        ccfile.write("[configcook]\nd = 'four'")
    file_path5 = os.path.join(tempdir, "file5.toml")
    with open(file_path5, "w") as ccfile:
        ccfile.write('[configcook]\nextends = ["file3.toml", "file4.toml"]\ne = 5')
    assert parse_toml_config(file_path5) == {
        "configcook": {
            "a": 1,
            "b": 2,
            "c": 3,
            "d": "four",
            "e": 5,
            "extends": ["file3.toml", "file1.toml", "file2.toml", "file4.toml"],
        }
    }


def test_parse_toml_config_non_list_extends(tmp_path):
    from configcook.config import parse_toml_config

    tempdir = str(tmp_path)
    file_path1 = os.path.join(tempdir, "file1.toml")
    # file 1 extends file 2, but as string instead of list
    with open(file_path1, "w") as ccfile:
        ccfile.write("[configcook]\nextends = 'file2.toml'\na = 1")
    file_path2 = os.path.join(tempdir, "file2.toml")
    with open(file_path2, "w") as ccfile:
        ccfile.write("[configcook]\nb = 2")
    with pytest.raises(ValueError):
        parse_toml_config(file_path1)


def test_parse_toml_config_plus_integer(tmp_path):
    from configcook.config import parse_toml_config

    tempdir = str(tmp_path)
    file_path1 = os.path.join(tempdir, "file1.toml")
    # file 1 extends file 2
    with open(file_path1, "w") as ccfile:
        ccfile.write('[configcook]\nextends = ["file2.toml"]\na = 1')
    # file 2 adds to a value of file 1
    file_path2 = os.path.join(tempdir, "file2.toml")
    with open(file_path2, "w") as ccfile:
        ccfile.write('[configcook]\n"a+" = 2')
    assert parse_toml_config(file_path1) == {
        "configcook": {"a": 3, "extends": ["file2.toml"]}
    }


def test_parse_toml_config_plus_list(tmp_path):
    from configcook.config import parse_toml_config

    tempdir = str(tmp_path)
    file_path1 = os.path.join(tempdir, "file1.toml")
    # file 1 extends file 2
    with open(file_path1, "w") as ccfile:
        ccfile.write('[configcook]\nextends = ["file2.toml"]\na = ["one"]')
    # file 2 adds to a value of file 1
    file_path2 = os.path.join(tempdir, "file2.toml")
    with open(file_path2, "w") as ccfile:
        ccfile.write('[configcook]\n"a+" = ["two"]')
    assert parse_toml_config(file_path1) == {
        "configcook": {"a": ["one", "two"], "extends": ["file2.toml"]}
    }


def test_parse_toml_config_plus_string(tmp_path):
    from configcook.config import parse_toml_config

    tempdir = str(tmp_path)
    file_path1 = os.path.join(tempdir, "file1.toml")
    # file 1 extends file 2
    with open(file_path1, "w") as ccfile:
        ccfile.write('[configcook]\nextends = ["file2.toml"]\na = "one"')
    # file 2 adds to a value of file 1
    file_path2 = os.path.join(tempdir, "file2.toml")
    with open(file_path2, "w") as ccfile:
        ccfile.write('[configcook]\n"a+" = "two"')
    assert parse_toml_config(file_path1) == {
        "configcook": {"a": "onetwo", "extends": ["file2.toml"]}
    }


def test_merge_dicts():
    from configcook.config import _merge_dicts as md
    from configcook.exceptions import ConfigError

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
    # We can add integers with +=.
    assert md({"a": 1}, {"a +": 2}) == {"a": 3}
    assert md({"a": 1}, {"a+": 2}) == {"a": 3}
    assert md({"a": 1}, {"a       +": 2}) == {"a": 3}
    # We can add floats with +=.
    assert md({"a": 1.2}, {"a +": 3.4}) == {"a": 4.6}
    # We can add strings with +=.
    assert md({"a": "a b"}, {"a +": "c\nd"}) == {"a": "a bc\nd"}
    assert md({"a": "a\nb"}, {"a +": "c d"}) == {"a": "a\nbc d"}
    # We can add lists with +=.
    assert md({"a": ["a", "b"]}, {"a +": ["c\nd"]}) == {"a": ["a", "b", "c\nd"]}
    # We can add booleans with +=.
    assert md({"a": False}, {"a +": False}) == {"a": 0}
    assert md({"a": False}, {"a +": True}) == {"a": 1}
    assert md({"a": True}, {"a +": False}) == {"a": 1}
    assert md({"a": True}, {"a +": True}) == {"a": 2}
    # We cannot add different types with +=.
    with pytest.raises(ConfigError):
        md({"a": 1}, {"a +": "2"})
    with pytest.raises(ConfigError):
        md({"a": 1}, {"a +": 1.0})
    with pytest.raises(ConfigError):
        md({"a": "1"}, {"a +": ["2"]})
    with pytest.raises(ConfigError):
        md({"a": 1}, {"a +": False})
