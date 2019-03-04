# -*- coding: utf-8 -*-
import logging
import sys


logger = logging.getLogger(__name__)


class Entrypoint(object):
    """configcook entrypoint.

    This is the basis for extensions and recipes.
    """

    is_extension = False
    is_recipe = False

    def __init__(self, name, config, options):
        self.name = name
        self.config = config
        self.options = options
        self.parse_options()

    def parse_options(self):
        """Do special handling on options if needed.
        """
        pass

    def require(self, name):
        """Require and return the name option.

        Raise an error if the option is not there.
        Empty is not allowed.
        """
        try:
            value = self.options[name]
        except KeyError:
            logger.error("Required option %s is missing from [%s].", name, self.name)
            sys.exit(1)
        if not value:
            logger.error("Required option %s is empty in [%s].", name, self.name)
            sys.exit(1)
        return value
