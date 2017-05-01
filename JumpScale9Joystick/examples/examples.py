from js9 import j

base = j.tools.cuisine._getBaseClassLoader()


class examples(base):

    def __init__(self, executor, cuisine):
        base.__init__(self, executor, cuisine)
