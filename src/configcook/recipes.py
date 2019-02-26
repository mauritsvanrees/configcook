# -*- coding: utf-8 -*-
import logging


logger = logging.getLogger(__name__)


class BaseRecipe(object):
    """Base cookconfig recipe."""

    def __init__(self, part_name, **options):
        self.part_name = part_name
        self.recipe_name = options.get('recipe', '')
        self.options = options

    def install(self):
        logger.info(
            'Calling install of part %s, recipe %s.',
            self.part_name,
            self.recipe_name,
        )


class ExampleRecipe(BaseRecipe):
    """Example cookconfig recipe.

    Probably want to move this to an examples directory.
    But for now okay.
    """
