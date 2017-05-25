from JumpScale import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineG8OSUfs(app):
    """
    """
    NAME = 'g8ufs'

    def build(self, start=False, install=True, reset=False):
        if reset is False and self.isInstalled():
            return

        self.cuisine.package.mdupdate()
        self.cuisine.package.install('build-essential')

        self.cuisine.development.golang.get("github.com/g8os/g8ufs")
        self.cuisine.core.file_copy("$GOPATHDIR/bin/g8ufs", "$BASEDIR/bin/")

        if install:
            self.install(start)
