# -*- coding: utf-8 -*-


class ConfigCookError(Exception):
    """Error in configcook.

    Used as base exception, and for cases that are not covered
    by more specific exceptions defined below.
    """

    def __str__(self):
        return " ".join(map(str, self.args))


class ConfigError(ConfigCookError):
    """Error in configuration.
    """


class LogicError(ConfigCookError):
    """Error in logic/programming.
    """
