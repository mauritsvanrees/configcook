# -*- coding: utf-8 -*-
from .config import parse_config
import logging
import sys


logger = logging.getLogger(__name__)


class ConfigCook(object):
    def __init__(self, options):
        self.options = options
        self.extensions = []
        self.recipes = []
        self.config = None
        logger.debug('Initialized ConfigCook.')

    def __call__(self):
        logger.debug('Calling ConfigCook.')

        logger.debug('Reading config.')
        self.config = parse_config('cc.cfg')
        logger.debug('Sections: %s', self.config.sections())
        if 'configcook' not in self.config.sections():
            logger.error("Section 'configcook' missing from config file.")
            sys.exit(1)
        logger.debug('configcook in sections.')
        if 'extensions' in self.config.options('configcook'):
            self.extensions = self.config.get('configcook', 'extensions').split()
            logger.debug(
                'extensions in configcook section: %s', self.extensions
            )
            self._load_extensions()

        logger.debug('End of ConfigCook call.')

    def _load_extensions(self):
        logger.debug('Loading extensions.')
        for extension in self.extensions:
            logger.warning('TODO: find and load extension %s', extension)
