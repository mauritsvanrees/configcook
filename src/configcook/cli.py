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

        # We could use traceback.print_exception to print the exception directly,
        # but we want to reuse the info later on.
        tb = traceback.format_exception(*exc_info)
        show_full_traceback = options.verbose or options.debug
        if show_full_traceback:
            # The traceback lines include line endings.
            print("".join(tb))
        if options.debug:
            sys.stderr.write("\nStarting pdb:\n")
            pdb.post_mortem(exc_info[2])

        # With buildout I have too often seen people overlook a buildout error,
        # so let's make it really clear here that something is wrong.
        print("*" * 80)
        print("***** CONFIGCOOK QUITS WITH AN ERROR!")
        print("***** Command line was: {0}".format(" ".join(sys.argv)))
        if not show_full_traceback:
            print("***** Use 'configcook --verbose' for a more detailed error message.")
        if options.debug:
            # If the user did some debugging in pdb, a different error may have been raised.
            print("***** The original error was:")
        else:
            print("***** The error is:")
        print("*****")
        # Print the last line of the traceback, which is the main exception message.
        print("***** {0}".format(tb[-1].strip()))
        # Note: if you end up here because you ran "pytest --pdb" and the sys.exit is not expected,
        # then you may want to start a pdb on the original exception:
        # pdb.post_mortem(exc_info[2])
        sys.exit(1)
