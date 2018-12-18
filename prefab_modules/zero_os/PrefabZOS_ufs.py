from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabZOS_ufs(app):
    """
    """
    NAME = 'g8ufs'

    def build(self, start=False, install=True, reset=False):
        if reset is False and self.isInstalled():
            return

        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install('build-essential')

        self.prefab.runtimes.golang.get("github.com/g8os/g8ufs")
        self.prefab.core.file_copy("{DIR_BASE}/go/bin/g8ufs", "{DIR_BASE}/bin/")

        if install:
            self.install(start)
