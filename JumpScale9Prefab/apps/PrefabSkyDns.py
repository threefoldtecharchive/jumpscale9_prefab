from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabSkyDns(app):
    NAME = "skydns"

    def build(self, start=True, install=True):
        if self.isInstalled():
            return
        self.prefab.development.golang.install()
        self.prefab.development.golang.get("github.com/skynetservices/skydns")
        if install:
            self.install(start)

    def install(self, start=True):
        """
        download , install, move files to appropriate places, and create relavent configs
        """
        self.prefab.core.file_copy(self.prefab.core.joinpaths('$GOPATHDIR', 'bin', 'skydns'), '$BINDIR')
        self.prefab.bash.addPath(self.replace("$BINDIR"))

        if start:
            self.start()

    def start(self):
        cmd = self.prefab.bash.cmdGetPath("skydns")
        self.prefab.processmanager.ensure("skydns", cmd + " -addr 0.0.0.0:53")
