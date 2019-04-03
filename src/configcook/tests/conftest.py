# -*- coding: utf-8 -*-
import os
import pytest
import sys


@pytest.fixture
def safe_sys_argv():
    orig_sys_argv = sys.argv.copy()
    yield
    sys.argv = orig_sys_argv


@pytest.fixture
def safe_working_dir():
    orig_working_dir = os.getcwd()
    yield
    # Note: we could compare os.getcwd() with the original, but os.getcwd()
    # will fail if the current working directory no longer exists.
    # So we always change the dir without comparing.
    os.chdir(orig_working_dir)
