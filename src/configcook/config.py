# -*- coding: utf-8 -*-
from ._vendor.configparser import parse
from copy import deepcopy
import os


class ConfigCookConfig(dict):
    """Configuration object for configcook.

    This is a wrapper around the standard Python dict class.
    In the init, it deepcopies the config to self._raw.
    Then we have an original, unchanged copy,
    without any enhancements or trickery.
    """

    def __init__(self, config):
        super(ConfigCookConfig, self).__init__(config)
        self._raw = deepcopy(config)


def parse_config(path):
    """Parse config with the configparser from zc.buildout.

    TODO: support 'extends = path1 path2'
    TODO: support urls
    """
    fpname = os.path.basename(path)
    with open(path) as fp:
        result = parse(fp, fpname)
    return ConfigCookConfig(result)
