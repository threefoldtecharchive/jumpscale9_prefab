from JumpScale import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineSyncthing(app):

    NAME = 'syncthing'

    @property
    def builddir(self):
        return self.cuisine.core.dir_paths['BUILDDIR'] + "/syncthing"

    def build(self, start=True, install=True, reset=False, version='v0.14.18'):
        """
        build and setup syncthing to run on :8384 , this can be changed from the config file in /optvar/cfg/syncthing
        version e.g. 'v0.14.5'
        """

        if self.doneGet("build") and not reset:
            return

        self.cuisine.development.golang.install()

        # build
        url = "https://github.com/syncthing/syncthing.git"
        if self.cuisine.core.file_exists('$GOPATHDIR/src/github.com/syncthing/syncthing'):
            self.cuisine.core.dir_remove('$GOPATHDIR/src/github.com/syncthing/syncthing')
        dest = self.cuisine.development.git.pullRepo(url,
                                                     dest='$GOPATHDIR/src/github.com/syncthing/syncthing',
                                                     ssh=False,
                                                     depth=1)

        if version is not None:
            self.cuisine.core.run("cd %s && go run build.go -version %s -no-upgrade" % (dest, version), profile=True)
        else:
            self.cuisine.core.run("cd %s && go run build.go" % dest, profile=True)

        # self.cuisine.core.dir_ensure(self.builddir+"/cfg")
        # self.cuisine.core.dir_ensure(self.builddir+"/bin")

        self.cuisine.core.copyTree(
            '$GOPATHDIR/src/github.com/syncthing/syncthing/bin',
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
        self.cuisine.development.pip.install("syncthing")

        self.cuisine.core.dir_ensure("$CFGDIR/syncthing")
        # self.cuisine.core.file_write("$CFGDIR/syncthing/syncthing.xml", config)

        self.cuisine.core.copyTree(self.builddir + "/bin", "$BINDIR")

        self.doneSet("install")

        if start:
            self.start()

    def start(self, reset=False):

        if reset:
            self.cuisine.core.run("killall syncthing", die=False)
            self.cuisine.core.run("rm -rf $CFGDIR/syncthing")

        if self.cuisine.core.dir_exists("$CFGDIR/syncthing") == False:
            self.cuisine.core.run(cmd="rm -rf $CFGDIR/syncthing;cd $BINDIR;./syncthing -generate  $CFGDIR/syncthing")
        pm = self.cuisine.processmanager.get("tmux")
        pm.ensure(name="syncthing", cmd="./syncthing -home  $CFGDIR/syncthing", path="$BINDIR")

    @property
    def apikey(self):
        import xml.etree.ElementTree as etree
        tree = etree.parse(self.replace("$CFGDIR/syncthing/config.xml"))
        r = tree.getroot()
        for item in r:
            if item.tag == "gui":
                for item2 in item:
                    self.logger.info(item2.tag)
                    if item2.tag == "apikey":
                        return item2.text

    def stop(self):
        pm = self.cuisine.processmanager.get("tmux")
        pm.stop("syncthing")

    def getApiClient(self):
        from IPython import embed
        self.logger.info("DEBUG NOW u8")
        embed()
        raise RuntimeError("stop debug here")
        import syncthing
        sync = syncthing.Syncthing(api_key=self.apikey, host="127.0.0.1", port=8384)
        sync.sys.config()
        return sync

    def restart(self):
        self.stop()
        self.start()
