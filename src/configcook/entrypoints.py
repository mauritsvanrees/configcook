# -*- coding: utf-8 -*-
from .utils import entrypoint_function
from .utils import set_defaults
import logging
import sys


logger = logging.getLogger(__name__)


class Entrypoint(object):
    """configcook entrypoint.

    This is the basis for extensions and recipes.
    """

    is_extension = False
    is_recipe = False
    defaults = {}

    def __init__(self, name, config, options):
        self.name = name
        self.config = config
        self.options = options
        self.parse_options()

    def parse_options(self):
        """Do special handling on options if needed.
        """
        if not self.defaults:
            pass
        set_defaults(self.defaults, self.options)

    @property
    @entrypoint_function
    def packages(self):
        # Look for option 'packages' with fallback to 'eggs'.
        for opt in ("packages", "eggs"):
            if opt in self.options:
                value = self.options[opt]
                if isinstance(value, (list, tuple)):
                    return value
                return value.split()
        return []
