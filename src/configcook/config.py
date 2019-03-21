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
            dirname = os.path.dirname(path)
            cc["extends"] = to_list(extends)
            # Build a new extends line that gets the correct order
            # for nested extends.
            new_extends = []
            for extend in cc["extends"]:
                new_extends.append(extend)
                if not os.path.isabs(extend):
                    extend = os.path.join(dirname, extend)
                extra_result = parse_config(extend)
                new_extends.extend(
                    extra_result.get("configcook", {}).get("extends", [])
                )
                result = _merge_dicts(result, extra_result)
            result["configcook"]["extends"] = new_extends
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
        if key.endswith("+"):
            # key += value
            plus = True
            key = key.rstrip("+").strip()
        else:
            plus = False
        if key not in result:
            result[key] = new_value
            continue
        if isinstance(new_value, dict):
            result[key] = _merge_dicts(result[key], new_value)
        else:
            # overwriting
            if plus:
                # a=b amended by a+=c becomes a=b\nc
                result[key] += "\n" + new_value
            else:
                result[key] = new_value
    return result
