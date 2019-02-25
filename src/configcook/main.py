# -*- coding: utf-8 -*-
from .config import parse_config
from .utils import execute_command
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
        # We could do self._pip('freeze') here as start to see what we have got.
        if 'extensions' in self.config.options('configcook'):
            self._extension_names = self.config.get(
                'configcook', 'extensions'
            ).split()
            logger.debug(
                'extensions in configcook section: %s', self._extension_names
            )
            self._load_extensions()

        logger.debug('End of ConfigCook call.')

    def _pip(self, *args):
        """Run a pip command in a shell."""
        # TODO: read extra pip options from configcook or maybe recipe
        # section.
        cmd = ['pip']
        cmd.extend(args)
        return execute_command(cmd)

    def _load_extensions(self):
        logger.debug('Loading extensions.')
        for extension_name in self._extension_names:
            self._load_extension(extension_name)
        logger.debug('Loaded extensions.')

    def _load_extension(self, extension_name):
        logger.debug('Loading extension %s.', extension_name)
        # This will either find an entrypoint or sys.exit(1).
        entrypoint = self._find_entrypoint(extension_name)
        # Instantiate the extension.
        # TODO: we probably want to pass something, like self.config.
        extension = entrypoint.load()
        logger.info('Loaded extension %s.', extension_name)
        self.extensions.append(extension)

    def _find_entrypoint(self, extension_name, install=True):
        """Find an entry point for this extension.

        When install=True, we can try a pip install.
        """
        logger.debug(
            'Searching entry point for extension  %s.', extension_name
        )
        group = 'configcook.extension'
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            if entrypoint.name == extension_name:
                logger.debug(
                    'Found entry point for extension %s.', extension_name
                )
                return entrypoint
        # Check if package is installed.
        # We probably want to support both package and package:name.
        package_name = extension_name.split(':')[0]
        try:
            pkg_resources.get_distribution(package_name)
        except pkg_resources.DistributionNotFound:
            # We do not have the package yet.  We can try to install it.
            pass
        else:
            # TODO: check dist.version.
            logger.error(
                'We have package %s but could not find a %s entrypoint '
                'with name %s.',
                package_name,
                group,
                extension_name,
            )
            sys.exit(1)
        if not install:
            logger.error(
                'We cannot install an entry point for extension %s.',
                extension_name,
            )
            sys.exit(1)
        logger.debug(
            'We do not yet have an entry point for extension %s.',
            extension_name,
        )
        logger.info('Trying to install package %s.', package_name)
        # TODO: catch error in this command.
        result = self._pip('install', package_name)
        print(result)
        # Retry, but this time do not allow to install.
        logger.info(
            'Retrying searching for entry point for extension %s after install of %s.',
            extension_name,
            package_name,
        )
        return self._find_entrypoint(extension_name, install=False)
