# -*- coding: utf-8 -*-
from .main import ConfigCook
from argparse import ArgumentParser

import logging
import sys


logger = logging.getLogger(__name__)


def parse_options():
    parser = ArgumentParser()
    # Note: please keep these sorted alphabetically on long form.
    parser.add_argument(
        "-c",
        "--config",
        # action="store_true",
        dest="configfile",
        default="cc.cfg",
        help="Config filename to load, if other than cc.cfg",
    )
    parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="Start Python debugger when exception occurs",
    )
    parser.add_argument(
        "--no-packages",
        action="store_true",
        dest="no_packages",
        default=False,
        help="Do not install, upgrade or uninstall Python packages. "
        "This also means no new extensions or recipes.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        help="Verbose mode",
    )
    options = parser.parse_args()
    return options


def main():
    options = parse_options()
    if options.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(level=loglevel, format="%(levelname)s: %(message)s")
    logger.debug("Only shown when --verbose is used.")
    logger.info("Hello, I will be your config cook today.")
    try:
        cook = ConfigCook(options)
        cook()
    except Exception:
        exc_info = sys.exc_info()
        import pdb
        import traceback

        traceback.print_exception(*exc_info)
        if options.debug:
            sys.stderr.write("\nStarting pdb:\n")
            pdb.post_mortem(exc_info[2])
        sys.exit(1)
