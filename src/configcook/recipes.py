# -*- coding: utf-8 -*-
from .utils import call_or_fail
from .utils import format_command_for_print
import logging
import sys


logger = logging.getLogger(__name__)


class BaseRecipe(object):
    """Base configcook recipe."""

    def __init__(self, name, config, options):
        self.name = name  # name of the part/section
        self.config = config
        self.options = options
        self.recipe_name = options.get('recipe', '')

    @property
    def packages(self):
        # Look for option 'packages' with fallback to 'eggs'.
        for opt in ('packages', 'eggs'):
            if opt in self.options:
                return self.options[opt].split()
        return []

    def install(self):
        logger.debug('Empty install for part %s.', self.name)


class CommandRecipe(BaseRecipe):
    """Basic configcook recipe that runs a command.
    """

    def install(self):
        command = self.options.get('command').split()
        if not command:
            # We could do this check earlier.
            logger.error(
                'part %s with recipe %s is missing the command option.',
                self.name,
                self.recipe_name,
            )
            sys.exit(1)
        logger.debug('Calling command: %s', format_command_for_print(command))
        call_or_fail(command)
