from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZOS_stor_client(base):
    def install(self):
        return self.prefab.runtimes.pip.install('http://home.maxux.net/wheelhouse/g8storclient-1.0-cp35-cp35m-manylinux1_x86_64.whl')
