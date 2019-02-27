# -*- coding: utf-8 -*-
from .configparser import parse
import os


def parse_config(path):
    # Use the configparser from zc.buildout.
    # TODO: support 'extends = path1 path2'
    # TODO: support urls
    fpname = os.path.basename(path)
    with open(path) as fp:
        return parse(fp, fpname)
