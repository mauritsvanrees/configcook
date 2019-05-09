# -*- coding: utf-8 -*-
from .config import parse_toml_config
from .exceptions import ConfigCookError
from .exceptions import ConfigError
from .exceptions import LogicError
from .utils import call_extensions
from .utils import call_or_fail
from .utils import format_command_for_print
from .utils import set_defaults
from .utils import to_path
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
    "bin-directory": {"default": "bin", "parser": to_path},
    # 'develop-eggs-directory': 'develop-eggs',
    # 'eggs-directory': 'eggs',
    # 'executable': sys.executable,
    "extends": {"default": [], "type": list},
    "fake-buildout": {"default": False, "type": bool},
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
        self._install_packages_from_extensions()

        # We will use @call_extensions around these functions.
        self.load_recipes()
        self.install_packages_from_recipes()
        self.run_recipes()

        logger.debug("End of ConfigCook call.")

    def _read_config(self):
        logger.debug("Reading config.")
        self.config = parse_toml_config(self.options.configfile)
        logger.debug("Sections: %s", ", ".join(self.config.keys()))
        if "configcook" not in self.config:
            raise ConfigError("Section 'configcook' missing from config file.")
        logger.debug("configcook in sections.")
        self._enhance_config()
        self._check_virtualenv()

    @call_extensions
    def pip(self, *args):
        """Run a pip command."""
        # TODO: read extra pip options from configcook or maybe recipe
        # section.  And allow setting environment variables?
        cmd = [self.config["configcook"]["pip"]]
        cmd.extend(args)
        if self.options.no_packages and ("install" in args or "uninstall" in args):
            raise ConfigError(
                "You want to install, upgrade or uninstall packages, "
                "but the --no-packages option prevents this. Refused to call command: {0}".format(
                    format_command_for_print(cmd)
                )
            )
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
            raise ConfigError("Missing parts option in configcook section.")
        parts = ccc["parts"]
        if not isinstance(parts, list):
            # We could turn "item1" into ["item1"] but we choose not too.
            # Would give problems with  "parts+"="item2" which could become "item1item2".
            raise ConfigError("parts option in configcook section must be a list.")
        for part in parts:
            if part not in self.config:
                raise ConfigError(
                    "[configcook] parts option has {0}, "
                    "but this is missing from the sections.".format(part)
                )
            # TODO: check dependencies between parts.
            self._part_names.append(part)
            self._load_part(part)

    def _find_and_install_packages(self, extensions=False, recipes=False):
        """Install packages from self.extensions or self.recipes."""
        if not (extensions or recipes):
            raise LogicError("Either extensions or recipes should be True.")
        if extensions and recipes:
            raise LogicError("extensions or recipes cannot both be True.")
        if extensions:
            sources = self.extensions
        else:
            sources = self.recipes
        all_packages = set()
        for source in sources:
            packages = getattr(source, "packages", [])
            logger.debug(
                "Part %s wants to install these packages: %s",
                source.name,
                ", ".join(packages),
            )
            all_packages.update(set(packages))
        logger.info(
            "Found %d packages to install (not including dependencies).",
            len(all_packages),
        )
        if not all_packages:
            return
        self._install_packages(*all_packages)

    def _install_packages_from_extensions(self):
        logger.debug(
            "Gathering list of all packages that the extensions want to install."
        )
        self._find_and_install_packages(extensions=True)

    @call_extensions
    def install_packages_from_recipes(self):
        logger.debug("Gathering list of all packages that the recipes want to install.")
        self._find_and_install_packages(recipes=True)

    def _install_packages(self, *packages):
        sorted_packages = sorted(packages, key=str.lower)
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
            options = self.config.get(name.replace(":", "_"), {})
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
        # This will either find an entrypoint or raise an exception.
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
            raise ConfigCookError(
                "We have package {0} but could not find a {1} entrypoint "
                "with name {2}.".format(package_name, group, name)
            )
        if not install:
            # We either do not want to allow installing at all, or this is
            # the second time we are called, and it has not helped.
            raise ConfigCookError(
                "We cannot install a package {0} to find a "
                "{1} entrypoint with name {2}".format(package_name, group, name)
            )
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
        # This will either find an entrypoint or raise an exception.
        entrypoint = self._find_recipe_entrypoint(name)
        # Load the entrypoint class.
        recipe_class = entrypoint.load()
        logger.debug("Loaded recipe %s.", recipe_class)
        return recipe_class

    def _load_part(self, name):
        options = self.config[name]
        if "recipe" not in options:
            raise ConfigError("recipe option missing from {0} section".format(name))
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
        logger.debug("Setting defaults for configcook section.")
        ccc = self.config["configcook"]
        set_defaults(DEFAULTS, ccc)

        # Add extra definitions in the configcook section
        ccc["executable"] = to_path(sys.executable)
        ccc["configcook-script"] = to_path(sys.argv[0])
        ccc["pip"] = to_path(os.path.join(ccc["bin-directory"], "pip"))
        configfile = to_path(self.options.configfile)
        ccc["configfile"] = configfile
        if "://" in configfile:
            # a url
            ccc["base-directory"] = os.getcwd()
        else:
            ccc["base-directory"] = os.path.dirname(configfile)

        # Maybe add buildout section as copy of configcook.
        if ccc["fake-buildout"]:
            # Make the configcook section available under the buildout name.
            # This may improve compatibility between configcook and buildout.
            self.config["buildout"] = ccc

        # Substitute ${part:name} in all options.
        self.config.substitute_all()

    def _check_virtualenv(self):
        """Check that we are in a virtualenv, or similar.

        Best seems to be to check that the bin-directory
        has python and pip executables.
        And possibly check that the current configcook script
        is in that directory too.
        """
        if self.options.no_packages:
            # We are not touching any packages, so it is safe to skip the virtualenv check.
            logger.debug("Option --no-packages used, so skipping the virtualenv check.")
            return
        ccc = self.config["configcook"]
        base_dir = ccc["base-directory"]
        bin_dir = ccc["bin-directory"]
        if not os.path.isdir(bin_dir):
            raise ConfigCookError(
                "[configcook] bin-directory ({0}) does not exist or is not "
                "a directory. Please create a virtualenv (or similar).".format(bin_dir)
            )
        bin_contents = os.listdir(bin_dir)
        for key in ("executable", "pip", "configcook-script"):
            script = ccc[key]
            script_dir = os.path.dirname(script)
            script_name = os.path.basename(script)
            # Is the script in the bin dir?
            if script_dir != bin_dir:
                # Dangerous.
                if key == "configcook-script" and script_dir.startswith(base_dir):
                    # When we start with 'python -m configcook' the script may be
                    # '.../src/configcook/__main__.py'.  That seems acceptable.
                    logger.debug(
                        "%s (%s) is not in [configcook] bin-directory (%r). "
                        "But it is within the base-directory (%r) so we accept it.",
                        key,
                        script,
                        bin_dir,
                        base_dir,
                    )
                    continue
                raise ConfigCookError(
                    "{0} ({1}) is not in [configcook] bin-directory ({2}). "
                    "Please create a virtualenv (or similar).".format(
                        key, script, bin_dir
                    )
                )
            # Does the script exist?
            if script_name not in bin_contents:
                raise ConfigCookError(
                    "[configcook] bin-directory ({0}) misses a {1} script. "
                    "Please create a virtualenv (or similar).".format(
                        bin_dir, script_name
                    )
                )
