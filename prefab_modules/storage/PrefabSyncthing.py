from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabSyncthing(app):

    NAME = 'syncthing'

    @property
    def builddir(self):
        return self.prefab.core.dir_paths['BUILDDIR'] + "/syncthing"

    def build(self, start=True, install=True, reset=False, version='v0.14.18'):
        """
        build and setup syncthing to run on :8384 , this can be changed from the config file in /optvar/cfg/syncthing
        version e.g. 'v0.14.5'
        """

        if self.doneGet("build") and not reset:
            return

        self.prefab.runtimes.golang.install()

        # build
        url = "https://github.com/syncthing/syncthing.git"
        if self.prefab.core.file_exists('{DIR_BASE}/go/src/github.com/syncthing/syncthing'):
            self.prefab.core.dir_remove('{DIR_BASE}/go/src/github.com/syncthing/syncthing')
        dest = self.prefab.tools.git.pullRepo(url,
                                                     dest='{DIR_BASE}/go/src/github.com/syncthing/syncthing',
                                                     ssh=False,
                                                     depth=1)

        if version is not None:
            self.prefab.core.run("cd %s && go run build.go -version %s -no-upgrade" % (dest, version), profile=True)
        else:
            self.prefab.core.run("cd %s && go run build.go" % dest, profile=True)

        # self.prefab.core.dir_ensure(self.builddir+"/cfg")
        # self.prefab.core.dir_ensure(self.builddir+"/bin")

        self.prefab.core.copyTree(
            '{DIR_BASE}/go/src/github.com/syncthing/syncthing/bin',
            self.builddir + "/bin",
            keepsymlinks=False,
            deletefirst=True,
            overwriteFiles=True,
            recursive=True,
            rsyncdelete=True,
            createdir=True,
            ignorefiles=[
                'testutil',
                'stbench'])

        self.doneSet("build")

        if install:
            self.install(start=start)

    def install(self, start=True, reset=False, homedir=""):
        """
        download, install, move files to appropriate places, and create relavent configs
        """

        if self.doneGet("install") and not reset:
            return

        self.build()
        self.prefab.runtimes.pip.install("syncthing")

        self.prefab.core.dir_ensure("$CFGDIR/syncthing")
        # self.prefab.core.file_write("$CFGDIR/syncthing/syncthing.xml", config)

        self.prefab.core.copyTree(self.builddir + "/bin", "{DIR_BIN}")

        self.doneSet("install")

        if start:
            self.start()

    def start(self, reset=False):

        if reset:
            self.prefab.core.run("killall syncthing", die=False)
            self.prefab.core.run("rm -rf $CFGDIR/syncthing")

        if self.prefab.core.dir_exists("$CFGDIR/syncthing") == False:
            self.prefab.core.run(cmd="rm -rf $CFGDIR/syncthing;cd {DIR_BIN};./syncthing -generate  $CFGDIR/syncthing")
        pm = self.prefab.system.processmanager.get("tmux")
        pm.ensure(name="syncthing", cmd="./syncthing -home  $CFGDIR/syncthing", path="{DIR_BIN}")

    @property
    def apikey(self):
        import xml.etree.ElementTree as etree
        tree = etree.parse(self.executor.replace("$CFGDIR/syncthing/config.xml"))
        r = tree.getroot()
        for item in r:
            if item.tag == "gui":
                for item2 in item:
                    self._logger.info(item2.tag)
                    if item2.tag == "apikey":
                        return item2.text

    def stop(self):
        pm = self.prefab.system.processmanager.get("tmux")
        pm.stop("syncthing")

    def getApiClient(self):
        from IPython import embed
        self._logger.info("DEBUG NOW u8")
        embed()
        raise RuntimeError("stop debug here")
        import syncthing
        sync = syncthing.Syncthing(api_key=self.apikey, host="127.0.0.1", port=8384)
        sync.sys.config()
        return sync

    def restart(self):
        self.stop()
        self.start()
