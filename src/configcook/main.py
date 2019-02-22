# -*- coding: utf-8 -*-
from .config import parse_config
import logging
import pkg_resources
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
            self._extension_names = self.config.get('configcook', 'extensions').split()
            logger.debug(
                'extensions in configcook section: %s', self._extension_names
            )
            self._load_extensions()

        logger.debug('End of ConfigCook call.')

    def _load_extensions(self):
        logger.debug('Loading extensions.')
        group = 'configcook.extension'
        entrypoints = list(pkg_resources.iter_entry_points(group=group))
        if not entrypoints:
            logger.error('No entrypoints have been registered for %s.', group)
            return

        for extension_name in self._extension_names:
            extension = None
            # Grab the function or class that is the actual plugin.
            for entrypoint in entrypoints:
                if entrypoint.name == extension_name:
                    logger.debug('Found entry point for extension %s.', extension_name)
                    break
            else:
                logger.error('Could not find entry point for extension %s.', extension_name)
                sys.exit(1)
            # Instantiate the extension.
            # TODO: we probably want to pass something, like self.config.
            extension = entrypoint.load()
            logger.debug('Loaded extension %s.', extension_name)
            self.extensions.append(extension)
