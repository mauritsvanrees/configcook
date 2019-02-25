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
        for name in self._extension_names:
            self._load_extension(name)
        logger.debug('Loaded extensions.')

    def _load_extension(self, name):
        logger.debug('Loading extension %s.', name)
        # This will either find an entrypoint or sys.exit(1).
        entrypoint = self._find_extension_entrypoint(name)
        # Instantiate the extension.
        # TODO: we probably want to pass something, like self.config.
        extension = entrypoint.load()
        logger.info('Loaded extension %s.', name)
        self.extensions.append(extension)

    def _find_entrypoint(self, group, name, install=True):
        """Find an entry point for this extension or recipe.

        - group is the entrypoint group: 'configcook.extension/recipe'
        - name is the entrypoint name: 'package.name', or
         'package.name:special' if a package has more than one entrypoint.
        - When install=True, we can try a pip install.
        """
        logger.debug('Searching %s entrypoint with name %s.', group, name)
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            if entrypoint.name == name:
                logger.debug('Found %s entrypoint with name %s.', group, name)
                return entrypoint
        # Check if package is installed.
        # We support both package and package:name.
        package_name = name.split(':')[0]
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
                name,
            )
            sys.exit(1)
        if not install:
            # We either do not want to allow installing at all, or this is
            # the second time we are called, and it has not helped.
            logger.error(
                'We cannot install a package %s to find a '
                '%s entrypoint with name %s.',
                package_name,
                group,
                name,
            )
            sys.exit(1)
        logger.debug(
            'We do not yet have a %s entrypoint with name %s.', group, name
        )
        logger.info('Trying to install package %s.', package_name)
        # TODO: catch error in this command.
        result = self._pip('install', package_name)
        print(result)
        # Retry, but this time do not allow to install.
        logger.info(
            'Retrying searching for %s entrypoint with name %s '
            'after install of package %s.',
            group,
            name,
            package_name,
        )
        return self._find_entrypoint(group, name, install=False)

    def _find_extension_entrypoint(self, name):
        """Find an entry point for this extension.
        """
        group = 'configcook.extension'
        return self._find_entrypoint(group, name)

    def _find_recipe_entrypoint(self, name):
        """Find an entry point for this recipe.
        """
        group = 'configcook.recipe'
        return self._find_entrypoint(group, name)
