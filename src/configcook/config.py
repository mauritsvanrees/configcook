# -*- coding: utf-8 -*-
from ._vendor.configparser import parse
import os


def parse_config(path):
    """Parse config with the configparser from zc.buildout.

    TODO: support 'extends = path1 path2'
    TODO: support urls

    IDEA: wrap own class around the returned dictionary.
    Add a ._raw attribute.
    """
    fpname = os.path.basename(path)
    with open(path) as fp:
        return parse(fp, fpname)
