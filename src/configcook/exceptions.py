# -*- coding: utf-8 -*-


class ConfigError(Exception):
    """Error in configuration.
    """

    def __str__(self):
        return " ".join(map(str, self.args))
