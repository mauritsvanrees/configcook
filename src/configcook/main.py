# -*- coding: utf-8 -*-
from .config import parse_config
from .utils import call_or_fail
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
        self._extension_names = []
        self._part_names = []
        logger.debug('Initialized ConfigCook.')

    def __call__(self):
        logger.debug('Calling ConfigCook.')

        logger.debug('Reading config.')
        self.config = parse_config('cc.cfg')
        logger.debug('Sections: %s', ', '.join(self.config.keys()))
        if 'configcook' not in self.config:
            logger.error("Section 'configcook' missing from config file.")
            sys.exit(1)
        logger.debug('configcook in sections.')
        # We could do self._pip('freeze') here as start to see what we have got.
        ccc = self.config['configcook']
        if 'extensions' in ccc:
            self._extension_names = self.config['configcook'][
                'extensions'
            ].split()
            logger.debug(
                'extensions in configcook section: %s',
                ', '.join(self._extension_names),
            )
            self._load_extensions()
            # TODO: let extensions do something.

        # Do we want all parts/sections/recipes?
        if 'parts' in ccc:
            parts = ccc['parts'].split()
        else:
            logger.error('Missing parts option in configcook section.')
            sys.exit(1)
        for part in parts:
            if part not in self.config:
                logger.error(
                    '[configcook] parts option has %s, '
                    'but this is missing from the sections.',
                    part,
                )
                sys.exit(1)
            # TODO: check dependencies between parts.
            self._part_names.append(part)
            self._load_part(part)

        logger.debug(
            'Gathering list of all packages that the recipes want to install.'
        )
        all_packages = set()
        for recipe in self.recipes:
            packages = getattr(recipe, 'packages', [])
            logger.debug(
                'Part %s wants to install these packages: %s',
                recipe.name,
                ', '.join(packages),
            )
            all_packages.update(set(packages))
        logger.info(
            'Recipes want to install %d packages (not including dependencies).',
            len(all_packages),
        )
        sorted_packages = sorted(all_packages, key=str.lower)
        logger.info('Full list of packages: %s', ', '.join(sorted_packages))
        if self.options.verbose:
            logger.debug('One package per line for easier viewing:')
            for package in sorted_packages:
                logger.debug(package)
        logger.info('Installing all packages.')
        # Note: we could call use pkg_resources to check if these packages
        # are already installed, but I guess pip is better at that.
        self._pip('install', *sorted_packages)

        for recipe in self.recipes:
            logger.debug(
                'Calling install of part %s, recipe %s.',
                recipe.name,
                recipe.recipe_name,
            )
            recipe.install()

        logger.debug('End of ConfigCook call.')

    def _pip(self, *args):
        """Run a pip command."""
        # TODO: read extra pip options from configcook or maybe recipe
        # section.
        cmd = ['pip']
        cmd.extend(args)
        # We could append --quiet in the commands that support it,
        # if self.options.verbose is False, but with 'install'
        # it is a bit too quiet: you don't see anything

        # Depending on which pip command we run, we may want to call
        # a different function.  For now we simply call the command,
        # and if this fails the program quits.
        call_or_fail(cmd)

    def _load_extensions(self):
        logger.debug('Loading extensions.')
        # All extensions use the options from configcook.
        options = self.config['configcook']
        for name in self._extension_names:
            extension_class = self._load_extension(name)
            # Instantiate the extension.
            extension = extension_class(name, self.config, options)
            logger.info('Loaded extension %s.', name)
            self.extensions.append(extension)
        logger.debug('Loaded extensions.')

    def _load_extension(self, name):
        logger.debug('Loading extension %s.', name)
        # This will either find an entrypoint or sys.exit(1).
        entrypoint = self._find_extension_entrypoint(name)
        # Load the entrypoint class.
        extension_class = entrypoint.load()
        logger.debug('Loaded extension %s.', extension_class)
        return extension_class

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
        self._pip('install', package_name)
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

    def _load_recipe(self, name):
        logger.debug('Loading recipe %s.', name)
        # This will either find an entrypoint or sys.exit(1).
        entrypoint = self._find_recipe_entrypoint(name)
        # Load the entrypoint class.
        recipe_class = entrypoint.load()
        logger.debug('Loaded recipe %s.', recipe_class)
        return recipe_class

    def _load_part(self, name):
        options = self.config[name]
        if 'recipe' not in options:
            logger.error('recipe option missing from %s section', name)
            sys.exit(1)
        recipe_name = options['recipe']
        recipe_class = self._load_recipe(recipe_name)
        # Instantiate the recipe.
        recipe = recipe_class(name, self.config, options)
        logger.info('Loaded part %s with recipe %s.', name, recipe_name)
        self.recipes.append(recipe)
