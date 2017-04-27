from js9 import j

base = j.tools.cuisine._getBaseClass()


class CuisineG8StoreClient(base):
    def install(self):
        self.cuisine.development.pip.install('g8storclient')
