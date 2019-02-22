# -*- coding: utf-8 -*-
import logging


logger = logging.getLogger(__name__)


class ConfigCook(object):
    def __init__(self, options):
        self.options = options
        logger.debug('Initialized ConfigCook.')

    def __call__(self):
        logger.debug('Calling ConfigCook.')
        logger.debug('End of ConfigCook call.')
