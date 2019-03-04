# -*- coding: utf-8 -*-
import logging
import pdb


logger = logging.getLogger(__name__)


class BaseExtension(object):
    """Base configcook extension.

    A zc.buildout extension gets the buildout object passed.
    For example, this is the init of mr.developer:

    def __init__(self, buildout):
        self.buildout = buildout
        self.buildout_dir = buildout['buildout']['directory']
        self.executable = sys.argv[0]

    """

    def __init__(self, name, config, options):
        self.name = name
        self.config = config
        self.options = options
        self.parse_options()

    def parse_options(self):
        """Do special handling on options if needed.
        """
        pass


class ExampleExtension(BaseExtension):
    """Example configcook extension.

    Probably want to move this to an examples directory.
    But for now okay.
    """


class PDBExtension(BaseExtension):
    """configcook extension that calls pdb.
    """

    def parse_options(self):
        self.before = self.options.get("before", "").split()
        self.after = self.options.get("after", "").split()

    def __call__(self):
        pdb.set_trace()

    def run_before(self, function_name, instance, *args, **kwargs):
        """A hook that is run before a function in configcook.

        instance is the configcook object.
        """
        if function_name not in self.before:
            return
        logger.info(
            "Entered PDB before calling configcook function %s "
            "with args %r and keyword args %r.",
            function_name,
            args,
            kwargs,
        )
        pdb.set_trace()

    def run_after(self, function_name, instance, *args, **kwargs):
        """A hook that is run after a function in configcook.

        instance is the configcook object.
        """
        if function_name not in self.after:
            return
        logger.info(
            "Entered PDB after calling configcook function %s "
            "with args %r and keyword args %r.",
            function_name,
            args,
            kwargs,
        )
        pdb.set_trace()
