# -*- coding: utf-8 -*-
from .configparser import parse
from six.moves.configparser import ConfigParser
import os


def standard_parse_config(path):
    parser = ConfigParser()
    parser.read([path])
    # TODO: support 'extends = path1 path2'
    # TODO: support urls
    return parser


def parse_config(path):
    # Use the configparser from zc.buildout.
    # TODO: support 'extends = path1 path2'
    # TODO: support urls
    fpname = os.path.basename(path)
    with open(path) as fp:
        return parse(fp, fpname)
