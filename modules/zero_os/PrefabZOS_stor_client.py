from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZOS_stor_client(base):
    def install(self):
        self.prefab.runtime.pip.install('g8storclient')
