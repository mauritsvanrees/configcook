# -*- coding: utf-8 -*-
from .entrypoints import Entrypoint
import logging
import pdb


logger = logging.getLogger(__name__)


class BaseExtension(Entrypoint):
    """Base configcook extension.
    """


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
