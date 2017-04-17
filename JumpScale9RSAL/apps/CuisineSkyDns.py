from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineSkyDns(app):
    NAME = "skydns"

    def build(self, start=True, install=True):
        if self.isInstalled():
            return
        self.cuisine.development.golang.install()
        self.cuisine.development.golang.get("github.com/skynetservices/skydns")
        if install:
            self.install(start)

    def install(self, start=True):
        """
        download , install, move files to appropriate places, and create relavent configs
        """
        self.cuisine.core.file_copy(self.cuisine.core.joinpaths('$GOPATHDIR', 'bin', 'skydns'), '$BINDIR')
        self.cuisine.bash.addPath(self.replace("$BINDIR"))

        if start:
            self.start()

    def start(self):
        cmd = self.cuisine.bash.cmdGetPath("skydns")
        self.cuisine.processmanager.ensure("skydns", cmd + " -addr 0.0.0.0:53")
