from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabG8OSUfs(app):
    """
    """
    NAME = 'g8ufs'

    def build(self, start=False, install=True, reset=False):
        if reset is False and self.isInstalled():
            return

        self.prefab.package.mdupdate()
        self.prefab.package.install('build-essential')

        self.prefab.development.golang.get("github.com/g8os/g8ufs")
        self.prefab.core.file_copy("$GOPATHDIR/bin/g8ufs", "$BASEDIR/bin/")

        if install:
            self.install(start)
