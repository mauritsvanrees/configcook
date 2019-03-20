# -*- coding: utf-8 -*-
from ._vendor.configparser import parse
from .utils import to_list
from .utils import to_path
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
    path = to_path(path)
    fpname = os.path.basename(path)
    with open(path) as fp:
        result = parse(fp, fpname)
    cc = result.get("configcook")
    if cc:
        extends = cc.get("extends")
        if extends:
            cc["extends"] = to_list(extends)
            dirname = os.path.dirname(path)
            for extend in cc["extends"]:
                if not os.path.isabs(extend):
                    extend = os.path.join(dirname, extend)
                extra_result = parse_config(extend)
                result = _merge_dicts(result, extra_result)
    return ConfigCookConfig(result)


def _merge_dicts(orig, new):
    """Merge two dictionaries.

    Actually, two ConfigCookConfig objects, but we can ignore that here.
    We are talking about dictionaries that contain dictionaries,
    which means orig.update(new) will not work.

    TODO: handle key += value
    """
    result = deepcopy(orig)
    for key, new_value in new.items():
        if key not in result:
            result[key] = new_value
            continue
        # if key == 'configcook' and 'extends' in result.get(key, {}):
        #     # Take care of extends.
        #     old_extends = result[key]['extends']
        if isinstance(new_value, dict):
            result[key] = _merge_dicts(result[key], new_value)
        elif isinstance(new_value, list):
            # likely [configcook] "extends"
            result[key].extend(new_value)
        else:
            # overwriting
            result[key] = new_value
    return result
