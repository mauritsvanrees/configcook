# -*- coding: utf-8 -*-
from .entrypoints import Entrypoint
from .utils import call_or_fail
from .utils import entrypoint_function
from .utils import substitute
from .utils import to_path
import logging
import os
import six
import sys


logger = logging.getLogger(__name__)


class BaseRecipe(Entrypoint):
    """Base configcook recipe."""

    is_recipe = True

    def parse_options(self):
        super(BaseRecipe, self).parse_options()
        self.recipe_name = self.options.get("recipe", "")

    @entrypoint_function
    def install(self):
        logger.debug("Empty install for part %s.", self.name)


# TODO update method?  When is that called?
# We don't yet have a .installed.cfg.


class CommandRecipe(BaseRecipe):
    """Basic configcook recipe that runs one or more commands.
    """

    defaults = {"command": {"required": True}}

    @entrypoint_function
    def install(self):
        commands = self.options["command"]
        if isinstance(commands, six.string_types):
            commands = [commands]
        for command in commands:
            if not command:
                continue
            logger.debug("Calling command: %s", command)
            command = command.split()
            call_or_fail(command)


class TemplateRecipe(BaseRecipe):
    """Basic configcook recipe that renders an inline template to a file.
    """

    defaults = {
        "input": {"required": True},
        "output": {"parser": to_path, "required": True},
    }

    @entrypoint_function
    def install(self):
        value = self.options["input"]
        output = self.options["output"]
        # ${configcook:parts} should become a list.
        value = substitute(self.config, value, current_part=self.name)
        with open(output, "w") as outfile:
            outfile.write(value)
        logger.info("Part %s wrote to output file %s", self.name, output)
        logger.debug("Value written: %r", value)
