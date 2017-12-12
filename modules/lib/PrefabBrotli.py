from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabBrotli(app):

    NAME = 'brotli'

    def _init(self):
        self.src_dir = "$TMPDIR/brotli"

    def build(self, reset=False):
        if reset is False and (self.isInstalled() or self.doneGet('build')):
            return
        cmake = self.prefab.development.cmake
        if not cmake.isInstalled():
            cmake.install()
        git_url = "https://github.com/google/brotli.git"
        self.prefab.tools.git.pullRepo(git_url, dest=self.src_dir, branch='master', depth=1, ssh=False)
        cmd = """
        cd {}
        mkdir out && cd out
        ../configure-cmake
        make
        make test
        """.format(self.src_dir)
        cmd = self.replace(cmd)
        self.prefab.core.run(cmd)
        self.doneSet('build')

    def install(self, reset=False):
        if reset is False and self.isInstalled():
            self.logger.info("Brotli already installed")
            return
        if not self.doneGet('build'):
            self.build()
        cmd = """
        cd {}/out
        make install
        """.format(self.src_dir)
        self.prefab.core.run(cmd)
        self.prefab.runtime.pip.install('brotli>=0.5.2')
