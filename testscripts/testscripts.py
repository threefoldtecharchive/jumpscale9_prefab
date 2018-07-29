from jumpscale import j

base = j.tools.prefab._getBaseClassLoader()


class testscripts(base):

    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)
