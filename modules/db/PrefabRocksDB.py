from jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabRocksDB(base):

    def build(self, reset=True, install=True):
        self.install(reset=reset)

    def install(self, reset=False):
        # install required packages to run.
        if self.doneCheck("install", reset):
            return
        self.prefab.runtimes.pip.install('http://home.maxux.net/wheelhouse/python_rocksdb-0.6.9-cp35-cp35m-manylinux1_x86_64.whl')

        self.doneSet("install")
