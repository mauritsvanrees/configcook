# -*- coding: utf-8 -*-
from six.moves.configparser import ConfigParser


def parse_config(path):
    parser = ConfigParser()
    parser.read([path])
    # TODO: support 'extends = path1 path2'
    # TODO: support urls
    return parser
