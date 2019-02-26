# -*- coding: utf-8 -*-
import logging


logger = logging.getLogger(__name__)


class BaseRecipe(object):
    """Base cookconfig recipe."""

    def __init__(self, name, config, options):
        self.name = name  # name of the part/section
        self.config = config
        self.options = options
        self.recipe_name = options.get('recipe', '')

    def install(self):
        logger.info(
            'Calling install of part %s, recipe %s.',
            self.name,
            self.recipe_name,
        )


class ExampleRecipe(BaseRecipe):
    """Example cookconfig recipe.

    Probably want to move this to an examples directory.
    But for now okay.
    """
