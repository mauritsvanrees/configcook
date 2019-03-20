# -*- coding: utf-8 -*-
import os


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
    orig = {'a': a_data}
    ccc = ConfigCookConfig(orig)
    assert ccc == orig
    assert ccc._raw == orig
    assert ccc._raw == ccc
    assert ccc is not orig
    assert ccc._raw is not orig
    assert ccc._raw is not ccc
    assert orig.get('a') == a_data
    assert ccc.get('a') == a_data
    assert ccc._raw.get('a') == a_data

    # Now change the original data
    a_data.append(2)
    assert ccc == orig
    assert ccc._raw != orig
    assert ccc._raw != ccc
    assert ccc is not orig
    assert ccc._raw is not orig
    assert ccc._raw is not ccc
    assert orig.get('a') == a_data
    assert ccc.get('a') == a_data
    assert ccc._raw.get('a') == [1]

    # Now change the data in our class.
    ccc['b'] = 42
    assert ccc != orig
    assert ccc._raw != orig
    assert ccc._raw != ccc
    assert ccc is not orig
    assert ccc._raw is not orig
    assert ccc._raw is not ccc
    assert orig.get('b') is None
    assert ccc.get('b') == 42
    assert ccc._raw.get('b') is None
