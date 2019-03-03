# -*- coding: utf-8 -*-
import logging
import pdb


logger = logging.getLogger(__name__)


class BaseExtension(object):
    """Base cookconfig extension.

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


class ExampleExtension(BaseExtension):
    """Example cookconfig extension.

    Probably want to move this to an examples directory.
    But for now okay.
    """


class PDBExtension(BaseExtension):
    """cookconfig extension that calls pdb.
    """

    def run_before(self, function_name, instance, *args, **kwargs):
        """A hook that is run before a function in configcook.

        instance is the configcook object.
        """
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
        logger.info(
            "Entered PDB after calling configcook function %s "
            "with args %r and keyword args %r.",
            function_name,
            args,
            kwargs,
        )
        pdb.set_trace()
