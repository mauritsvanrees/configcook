# -*- coding: utf-8 -*-
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
