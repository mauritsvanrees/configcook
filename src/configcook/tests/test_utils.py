# -*- coding: utf-8 -*-
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
