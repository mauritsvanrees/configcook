# -*- coding: utf-8 -*-
from .config import parse_config
from .utils import call_extensions
from .utils import call_or_fail
from .utils import to_bool
from copy import deepcopy
import logging
import os
import pkg_resources
import sys


logger = logging.getLogger(__name__)


# Defaults for the configcook section.
# Taken over from _buildout_default_options for inspiration,
# but most of them commented out for now.
DEFAULTS = {
    # 'allow-hosts': '*',
    # 'allow-picked-versions': 'true',
    # 'allow-unknown-extras': 'false',
    "bin-directory": "bin",
    # 'develop-eggs-directory': 'develop-eggs',
    # 'eggs-directory': 'eggs',
    # 'executable': sys.executable,
    "fake-buildout": False,
    # 'find-links': '',
    # 'install-from-cache': 'false',
    # 'installed': '.installed.cfg',
    # 'log-format': '',
    # 'log-level': 'INFO',
    # 'newest': 'true',
    # 'offline': 'false',
    # 'parts-directory': 'parts',
    # 'prefer-final': 'true',
    # 'python': 'buildout',
    # 'show-picked-versions': 'false',
    # 'socket-timeout': '',
    # 'update-versions-file': '',
    # 'use-dependency-links': 'true',
}


class ConfigCook(object):
    def __init__(self, options):
        self.options = options
        self.extensions = []
        self.recipes = []
        self.config = None
        self._extension_names = []
        self._part_names = []
        logger.debug("Initialized ConfigCook.")

    def __call__(self):
        logger.debug("Calling ConfigCook.")

        self._read_config()
        self._load_extensions()

        # We will use @call_extensions around these functions.
        self.load_recipes()
        self.install_packages_from_recipes()
        self.run_recipes()

        logger.debug("End of ConfigCook call.")

    def _read_config(self):
        logger.debug("Reading config.")
        self.config = parse_config("cc.cfg")
        logger.debug("Sections: %s", ", ".join(self.config.keys()))
        if "configcook" not in self.config:
            logger.error("Section 'configcook' missing from config file.")
            sys.exit(1)
        logger.debug("configcook in sections.")
        self._enhance_config()
        self._check_virtualenv()

    @call_extensions
    def pip(self, *args):
        """Run a pip command."""
        # TODO: read extra pip options from configcook or maybe recipe
        # section.
        cmd = [self.config["configcook"]["pip"]]
        cmd.extend(args)
        # We could append --quiet in the commands that support it,
        # if self.options.verbose is False, but with 'install'
        # it is a bit too quiet: you don't see anything

        # Depending on which pip command we run, we may want to call
        # a different function.  For now we simply call the command,
        # and if this fails the program quits.
        call_or_fail(cmd)

    @call_extensions
    def load_recipes(self, *args):
        # Do we want all parts/sections/recipes?
        ccc = self.config["configcook"]
        if "parts" not in ccc:
            logger.error("Missing parts option in configcook section.")
            sys.exit(1)
        parts = ccc["parts"].split()
        for part in parts:
            if part not in self.config:
                logger.error(
                    "[configcook] parts option has %s, "
                    "but this is missing from the sections.",
                    part,
                )
                sys.exit(1)
            # TODO: check dependencies between parts.
            self._part_names.append(part)
            self._load_part(part)

    @call_extensions
    def install_packages_from_recipes(self, *args):
        logger.debug("Gathering list of all packages that the recipes want to install.")
        all_packages = set()
        for recipe in self.recipes:
            packages = getattr(recipe, "packages", [])
            logger.debug(
                "Part %s wants to install these packages: %s",
                recipe.name,
                ", ".join(packages),
            )
            all_packages.update(set(packages))
        logger.info(
            "Recipes want to install %d packages " "(not including dependencies).",
            len(all_packages),
        )
        if not all_packages:
            return
        sorted_packages = sorted(all_packages, key=str.lower)
        logger.info("Full list of packages: %s", ", ".join(sorted_packages))
        if self.options.verbose:
            logger.debug("One package per line for easier viewing:")
            for package in sorted_packages:
                logger.debug(package)
        logger.info("Installing all packages.")
        # Note: we could use pkg_resources to check if these packages
        # are already installed, but I guess pip is better at that.
        self.pip("install", *sorted_packages)

    @call_extensions
    def run_recipes(self):
        for recipe in self.recipes:
            recipe.install()

    def _load_extensions(self):
        # We could do self._pip('freeze') here as start
        # to see what we have got.
        ccc = self.config["configcook"]
        if "extensions" not in ccc:
            logger.debug("No extensions in config.")
            return
        self._extension_names = self.config["configcook"]["extensions"].split()
        logger.debug(
            "extensions in configcook section: %s", ", ".join(self._extension_names)
        )
        logger.debug("Loading extensions.")
        for name in self._extension_names:
            extension_class = self._load_extension(name)
            # Get the extension options from section [name].
            # If you use 'extension:name' in the config,
            # you likely get a parse error,
            # because 'name' is tried as a section condition.
            # Not quite what we want.
            # Try 'extension_name' then.
            options = self.config.get(name.replace(":", "_"))
            if options:
                # Let the extension work on a copy, so it is isolated
                # from possible changes to the main config.
                options = deepcopy(options)
            # Instantiate the extension and call it.
            extension = extension_class(name, self.config, options)
            if callable(extension):
                extension()
            logger.info("Loaded extension %s.", name)
            self.extensions.append(extension)
        logger.debug("Loaded extensions.")

    def _load_extension(self, name):
        logger.debug("Loading extension %s.", name)
        # This will either find an entrypoint or sys.exit(1).
        entrypoint = self._find_extension_entrypoint(name)
        # Load the entrypoint class.
        extension_class = entrypoint.load()
        logger.debug("Loaded extension %s.", extension_class)
        return extension_class

    def _find_entrypoint(self, group, name, install=True):
        """Find an entry point for this extension or recipe.

        - group is the entrypoint group: 'configcook.extension/recipe'
        - name is the entrypoint name: 'package.name', or
         'package.name:special' if a package has more than one entrypoint.
        - When install=True, we can try a pip install.
        """
        logger.debug("Searching %s entrypoint with name %s.", group, name)
        for entrypoint in pkg_resources.iter_entry_points(group=group):
            if entrypoint.name == name:
                logger.debug("Found %s entrypoint with name %s.", group, name)
                return entrypoint
        # Check if package is installed.
        # We support both package and package:name.
        package_name = name.split(":")[0]
        try:
            pkg_resources.get_distribution(package_name)
        except pkg_resources.DistributionNotFound:
            # We do not have the package yet.  We can try to install it.
            pass
        else:
            # TODO: check dist.version.
            logger.error(
                "We have package %s but could not find a %s entrypoint "
                "with name %s.",
                package_name,
                group,
                name,
            )
            sys.exit(1)
        if not install:
            # We either do not want to allow installing at all, or this is
            # the second time we are called, and it has not helped.
            logger.error(
                "We cannot install a package %s to find a "
                "%s entrypoint with name %s.",
                package_name,
                group,
                name,
            )
            sys.exit(1)
        logger.debug("We do not yet have a %s entrypoint with name %s.", group, name)
        logger.info("Trying to install package %s.", package_name)
        self.pip("install", package_name)
        # Retry, but this time do not allow to install.
        logger.info(
            "Retrying searching for %s entrypoint with name %s "
            "after install of package %s.",
            group,
            name,
            package_name,
        )
        return self._find_entrypoint(group, name, install=False)

    def _find_extension_entrypoint(self, name):
        """Find an entry point for this extension.
        """
        group = "configcook.extension"
        return self._find_entrypoint(group, name)

    def _find_recipe_entrypoint(self, name):
        """Find an entry point for this recipe.
        """
        group = "configcook.recipe"
        return self._find_entrypoint(group, name)

    def _load_recipe(self, name):
        logger.debug("Loading recipe %s.", name)
        # This will either find an entrypoint or sys.exit(1).
        entrypoint = self._find_recipe_entrypoint(name)
        # Load the entrypoint class.
        recipe_class = entrypoint.load()
        logger.debug("Loaded recipe %s.", recipe_class)
        return recipe_class

    def _load_part(self, name):
        options = self.config[name]
        if "recipe" not in options:
            logger.error("recipe option missing from %s section", name)
            sys.exit(1)
        recipe_name = options["recipe"]
        recipe_class = self._load_recipe(recipe_name)
        # Instantiate the recipe.
        recipe = recipe_class(name, self.config, options)
        logger.info("Loaded part %s with recipe %s.", name, recipe_name)
        self.recipes.append(recipe)

    def _enhance_config(self):
        """Enhance our configuration.

        self.config is a dict of dicts.
        We can add information, especially to the configcook section.
        """
        # Set defaults for configcook section.
        ccc = self.config["configcook"]
        for key, default in DEFAULTS.items():
            if key not in ccc:
                logger.debug("Set [configcook] %s option to default %r.", key, default)
                ccc[key] = default
            elif isinstance(default, bool):
                # Turn the user supplied value into a boolean.
                ccc[key] = to_bool(ccc[key])
        # TODO: interpolate ${part:name} in all options.
        # TODO: call os.path.expanduser on all options.
        # TODO: turn all known paths to real paths.
        ccc["bin-directory"] = os.path.realpath(
            os.path.expanduser(ccc["bin-directory"])
        )
        ccc["executable"] = os.path.realpath(os.path.expanduser(sys.executable))
        ccc["configcook-script"] = os.path.realpath(os.path.expanduser(sys.argv[0]))
        ccc["pip"] = os.path.join(ccc["bin-directory"], "pip")

        # Call this last.
        if ccc["fake-buildout"]:
            # Make the configcook section available under the buildout name.
            # This may improve compatibility between configcook and buildout.
            self.config["buildout"] = ccc

    def _check_virtualenv(self):
        """Check that we are in a virtualenv, or similar.

        Best seems to be to check that the bin-directory
        has python and pip executables.
        And possibly check that the current configcook script
        is in that directory too.
        """
        ccc = self.config["configcook"]
        bin_dir = ccc["bin-directory"]
        if not os.path.isdir(bin_dir):
            logger.error(
                "[configcook] bin-directory (%r) does not exist or is not "
                "a directory. Please create a virtualenv (or similar).",
                bin_dir,
            )
            sys.exit(1)
        bin_contents = os.listdir(bin_dir)
        for key in ("executable", "pip", "configcook-script"):
            script = ccc[key]
            script_dir = os.path.dirname(script)
            script_name = os.path.basename(script)
            # Is the script in the bin dir?
            if script_dir != bin_dir:
                logger.error(
                    "%s (%s) is not in [configcook] bin-directory (%r). "
                    "Please create a virtualenv (or similar).",
                    key,
                    ccc["executable"],
                    bin_dir,
                )
                sys.exit(1)
            # Does the script exist?
            if script_name not in bin_contents:
                logger.error(
                    "[configcook] bin-directory (%r) misses a %s script. "
                    "Please create a virtualenv (or similar).",
                    bin_dir,
                    script_name,
                )
                sys.exit(1)
