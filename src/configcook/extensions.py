# -*- coding: utf-8 -*-
class BaseExtension(object):
    """Base cookconfig extension."""

    def __init__(self, name, config, options):
        self.name = name
        self.config = config
        self.options = options


class ExampleExtension(BaseExtension):
    """Example cookconfig extension.

    Probably want to move this to an examples directory.
    But for now okay.
    """
