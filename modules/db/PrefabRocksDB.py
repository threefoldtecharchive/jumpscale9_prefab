from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabRocksDB(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/rocksdb/")

    def build(self, reset=True, install=True):
        # Get binaries and build rocksdb.
        if self.doneCheck("build", reset):
            return

        self.prefab.core.dir_ensure(self.BUILDDIRL)

        build_script = """
        #!/bin/bash

        set -x

        apt-get update
        apt-get install -y build-essential cmake libsnappy-dev zlib1g-dev libbz2-dev libgflags-dev liblz4-dev git python3-pip python-dev
        git clone https://github.com/facebook/rocksdb.git
        cd rocksdb
        mkdir -p build && cd build
        # cmake ..
        PORTABLE=1 make shared_lib
        make install
        ldconfig

        cd ../
        pip3 install -U setuptools>=25
        pip3 install python-rocksdb==0.6.9
        """
        j.tools.prefab.local.core.execute_script(build_script,
                                                 die=True,
                                                 profile=False,
                                                 interpreter='bash',
                                                 tmux=False,
                                                 replace=False,
                                                 showout=True,
                                                 sudo=False)

        self.doneSet("build")
        self.doneSet("install")

    def install(self, reset=False):
        # install required packages to run.
        if self.doneCheck("install", reset):
            return
        self.prefab.system.package.install("libhiredis-dev")
        self.prefab.system.package.install("libbz2-dev")
        self.prefab.system.package.install('python3-dev')
        self.prefab.runtimes.pip.ensure()
        self.prefab.runtimes.pip.multiInstall(['pyrocksdb', 'peewee'])

        self.doneSet("install")
