# -*- coding: utf-8 -*-
from six.moves.configparser import ConfigParser


def parse_config(path):
    parser = ConfigParser()
    parser.read([path])
    return parser
