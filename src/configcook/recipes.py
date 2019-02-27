# -*- coding: utf-8 -*-
from .utils import call_or_fail
from .utils import recipe_function
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

    def require(self, name):
        """Require and return the name option.

        Raise an error if the option is not there.
        Empty is not allowed.
        """
        try:
            value = self.options[name]
        except KeyError:
            logger.error(
                'Required option %s is missing from part %s.', name, self.name
            )
            sys.exit(1)
        if not value:
            logger.error(
                'Required option %s is empty in part %s.', name, self.name
            )
            sys.exit(1)
        return value

    @property
    @recipe_function
    def packages(self):
        # Look for option 'packages' with fallback to 'eggs'.
        for opt in ('packages', 'eggs'):
            if opt in self.options:
                return self.options[opt].split()
        return []

    @recipe_function
    def install(self):
        logger.debug('Empty install for part %s.', self.name)


# TODO update method?  When is that called?
# We don't yet have a .installed.cfg.


class CommandRecipe(BaseRecipe):
    """Basic configcook recipe that runs one or more commands.
    """

    @recipe_function
    def install(self):
        cmds = self.require('command').strip().splitlines()
        for command in cmds:
            if not command:
                continue
            logger.debug('Calling command: %s', command)
            command = command.split()
            call_or_fail(command)


class TemplateRecipe(BaseRecipe):
    """Basic configcook recipe that renders an inline template to a file.
    """

    @recipe_function
    def install(self):
        value = self.require('input')
        output = self.require('output')
        # TODO: expand variables in input:
        # ${configcook:parts} should become a list.
        # ~ should become /home/maurits.
        with open(output, 'w') as outfile:
            outfile.write(value)
        logger.debug('Wrote to output file %s', outfile)
        logger.debug('Value written: %r', value)
