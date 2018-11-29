from Jumpscale import j

app = j.tools.prefab._getBaseAppClass()

class PrefabSkyDns(app):

    def build(self, start=True, install=True):
        if self.isInstalled():
            return
        self.prefab.runtimes.golang.install()
        self.prefab.runtimes.golang.get("github.com/skynetservices/skydns")
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
        pm = self.prefab.system.processmanager.get()
        pm.ensure("skydns", cmd + " -addr 0.0.0.0:53")
