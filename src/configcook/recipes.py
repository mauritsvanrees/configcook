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
    """Basic configcook recipe that runs one or more commands.
    """

    def install(self):
        cmds = self.options.get('command').strip().splitlines()
        if not cmds:
            # We could do this check earlier.
            logger.error(
                'part %s with recipe %s is missing the command option.',
                self.name,
                self.recipe_name,
            )
            sys.exit(1)
        for command in cmds:
            if not command:
                continue
            logger.debug('Calling command: %s', command)
            command = command.split()
            call_or_fail(command)
