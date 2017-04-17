from JumpScale import j

base = j.tools.cuisine._getBaseClassLoader()


class testscripts(base):

    def __init__(self, executor, cuisine):
        base.__init__(self, executor, cuisine)
