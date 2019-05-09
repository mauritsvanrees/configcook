# -*- coding: utf-8 -*-
from .exceptions import ConfigError
from .utils import substitute
from .utils import to_path
from copy import deepcopy
import os
import toml


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

    def substitute_all(self):
        """Substitute/interpolate ${part:name} in all options."""
        # First interpolate in configcook section?
        # It might be tricky allow configcook to interpolate from other sections.
        # if "configcook" in self:
        #     self.substitute_section("configcook")
        for key in self:
            self.substitute_section(key)

    def substitute_section(self, section_name):
        """Substitute/interpolate ${part:name} in one section."""
        changed = False
        section = self[section_name]
        for key, value in section.items():
            new_value = substitute(self, value, current_part=section_name)
            if new_value == value:
                continue
            section[key] = new_value
            # TODO: do something with 'changed' value.
            # I think my idea was to do this recursively, and then we can
            # use this to know when we are done.
            changed = True


def parse_toml_config(path):
    """Parse config with toml.

    TODO: support 'extends = path1 path2'
    TODO: support urls
    """
    path = to_path(path)
    with open(path) as fp:
        result = toml.load(fp)
    cc = result.get("configcook")
    if cc:
        extends = cc.get("extends")
        if extends:
            if not isinstance(extends, list):
                raise ValueError(
                    "Option extends must be of type list. Got type: {0} ({1}).".format(
                        type(extends), extends
                    )
                )
            dirname = os.path.dirname(path)
            # Build a new extends line that gets the correct order
            # for nested extends.
            new_extends = []
            for extend in cc["extends"]:
                new_extends.append(extend)
                if not os.path.isabs(extend):
                    extend = os.path.join(dirname, extend)
                extra_result = parse_toml_config(extend)
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

    We allow appending to values, like zc.buildout does.
    With buildout we have this:

    a=b amended by a+=c becomes a=b\nc

    With toml, this must be different.
    Lists are pretty simple, we might want to require them:

    a=["b"] amended by "a+"=["c"] becomes a=["b", "c"]

    Note the "a+" quoted key, otherwise you get a parse error.

    Theoretically we could allow other values.
    For strings this could be a source of surprise for users.
    But could still be useful:

    base.toml:       title="Site"
    testing.toml:    "title+"=" testing"
    production.toml: "title+"=" production"
    On testing    this would become title="Site testing"
    On production this would become title="Site production"

    For integers (and floats) this could actually be useful.
    port=8080 amended by "port+"=100 becomes port=8180

    Booleans would work too:

    switch=False    -> False
    "switch+"=False -> 0
    "switch+"=True  -> 1

    As long as the two values have the same type, this seems safe.

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
                if type(result[key]) != type(new_value):
                    raise ConfigError(
                        "Conflicting types when adding to key {0}: cannot add {1} and {2}.".format(
                            key, type(result[key]), type(new_value)
                        )
                    )
                result[key] += new_value
            else:
                result[key] = new_value
    return result
