# -*- coding: utf-8 -*-
from .main import ConfigCook
from argparse import ArgumentParser

import logging


logger = logging.getLogger(__name__)


def parse_options():
    parser = ArgumentParser()
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
    cook = ConfigCook(options)
    cook()
