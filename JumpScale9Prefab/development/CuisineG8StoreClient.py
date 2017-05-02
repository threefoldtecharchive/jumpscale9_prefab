from js9 import j

base = j.tools.prefab._getBaseClass()


class CuisineG8StoreClient(base):
    def install(self):
        self.prefab.development.pip.install('g8storclient')
