from js9 import j

base = j.tools.prefab._getBaseClassLoader()


class examples(base):

    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)
