from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabCmake(app):
    NAME = 'cmake'

    def _init(self):
        self.src_dir = "$TMPDIR/cmake"

    def build(self):
        self.prefab.core.dir_ensure(self.src_dir)
        cmake_url = "https://cmake.org/files/v3.8/cmake-3.8.2.tar.gz"
        self.prefab.core.file_download(cmake_url, to=self.src_dir, overwrite=False, expand=True, removeTopDir=True)
        cmd = """
        cd %s && ./bootstrap && make
        """ % self.src_dir
        self.prefab.core.run(cmd)
        return

    def install(self):
        if self.isInstalled():
            return
        if not self.prefab.core.exists(self.src_dir):
            self.build()
        cmd = """
        cd %s && make install
        """ % self.src_dir
        self.prefab.core.run(cmd)
        return
