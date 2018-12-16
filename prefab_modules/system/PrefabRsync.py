from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabRsync(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("{DIR_VAR}/build/rsync/")
        self.VERSION = 'rsync-3.1.2'

    def reset(self):
        self.core.dir_remove(self.BUILDDIRL)
        self.doneDelete("build")

    def build(self, reset=False, install=True):
        """
        """

        if reset:
            self.reset()

        if self.doneGet("build") and not reset:
            return

        self.prefab.core.dir_ensure(self.BUILDDIRL)

        self.prefab.system.package.ensure("gcc")
        self.prefab.system.package.ensure("g++")
        self.prefab.system.package.ensure('make')

        self.prefab.core.file_download(
            "https://download.samba.org/pub/rsync/src/%s.tar.gz" %
            self.VERSION, to="%s/%s.tar.gz" %
            (self.BUILDDIRL, self.VERSION))

        C = """
        set -xe
        cd {DIR_VAR}/build/L
        tar -xf $VERSION.tar.gz
        cd $VERSION
        ./configure
        make
        """
        C = C.replace('{DIR_VAR}/build/L', self.BUILDDIRL)
        C = C.replace('$VERSION', self.VERSION)
        self.prefab.core.run(C, profile=True)

        self.doneSet("build")
        if install:
            self.install()

    def install(self,build=False):
        if build:
            if not self.doneGet("build"):
                self.build(install=False)
            self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("{DIR_BIN}"))
            self.prefab.bash.profileDefault.save()
            self.prefab.core.file_copy(
                "%s/%s/rsync" %
                (self.BUILDDIRL,
                self.VERSION),
                '{DIR_BIN}')
        else:
            self.prefab.system.package.install("rsync")

    def configure(self):
        self.install(build=False)
        
