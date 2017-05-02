from js9 import j

base = j.tools.prefab._getBaseClassLoader()


class development(base):

    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)
