from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabBrotli(app):

    NAME = 'brotli'

    def _init(self):
        self.src_dir = "$TMPDIR/brotli"

    def build(self, reset=False):
        if reset is False and self.isInstalled():
            return
        cmake = self.prefab.development.cmake
        if not cmake.isInstalled():
            cmake.install()
        git_url = "https://github.com/google/brotli.git"
        self.prefab.development.git.pullRepo(git_url, dest=self.src_dir, branch='master', depth=1, ssh=False)
        cmd = """
        cd {}
        mkdir out && cd out
        ../configure-cmake
        make
        make test
        """.format(self.src_dir)
        cmd = self.replace(cmd)
        self.prefab.core.run(cmd)

    def install(self, reset=False):
        if reset is False and self.isInstalled():
            self.logger.info("Brotli already installed")
            return
        if not self.prefab.core.exists("%s/out" % self.src_dir):
            self.build()
        cmd = """
        cd {}/out
        make install
        """.format(self.src_dir)
        self.prefab.core.run(cmd)
        self.prefab.development.pip.install('brotli>=0.5.2')
