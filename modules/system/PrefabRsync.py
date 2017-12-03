from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabRsync(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/rsync/")
        self.VERSION = 'rsync-3.1.2'

    def reset(self):
        self.core.dir_remove(self.BUILDDIRL)

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
        cd $BUILDDIRL
        tar -xf $VERSION.tar.gz
        cd $VERSION
        ./configure
        make
        """
        C = C.replace('$BUILDDIRL', self.BUILDDIRL)
        C = C.replace('$VERSION', self.VERSION)
        self.prefab.core.run(C, profile=True)

        self.doneSet("build")
        if install:
            self.install()

    def install(self):
        if not self.doneGet("build"):
            self.build(install=False)

        self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("$BINDIR"))
        self.prefab.bash.profileDefault.save()
        self.prefab.core.file_copy(
            "%s/%s/rsync" %
            (self.BUILDDIRL,
             self.VERSION),
            self.prefab.core.dir_paths['BINDIR'])
