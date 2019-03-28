# -*- coding: utf-8 -*-
import pytest
import sys


@pytest.fixture
def safe_sys_argv():
    orig_sys_argv = sys.argv.copy()
    yield
    sys.argv = orig_sys_argv
