
from jumpscale import j
# import os


app = j.tools.prefab._getBaseAppClass()


class PrefabGolang(app):

    NAME = 'go'

    def reset(self):
        if self.prefab.bash.profileDefault.envExists("GOPATH"):
            go_path = self.prefab.bash.profileDefault.envGet("GOPATH")
            self.prefab.bash.profileDefault.pathDelete(go_path)
        if self.prefab.bash.profileDefault.envExists("GOROOT"):
            go_root = self.prefab.bash.profileDefault.envGet("GOROOT")
            self.prefab.bash.profileDefault.pathDelete(go_root)
            self.prefab.bash.profileJS.pathDelete(go_root)

        self.prefab.bash.profileDefault.deleteAll("GOPATH")
        self.prefab.bash.profileJS.deleteAll("GOPATH")

        self.prefab.bash.profileDefault.deleteAll("GOROOT")
        self.prefab.bash.profileJS.deleteAll("GOROOT")

        self.prefab.bash.profileDefault.deleteAll("GOGITSDIR")
        self.prefab.bash.profileJS.deleteAll("GOGITSDIR")

        self.prefab.bash.profileDefault.pathDelete("/go/")
        self.prefab.bash.profileJS.pathDelete("/go/")

        # ALWAYS SAVE THE DEFAULT FIRST !!!
        self.prefab.bash.profileDefault.save()
        self.prefab.bash.profileJS.save()

        self._init()

    def _init(self):
        self.GOROOTDIR = self.prefab.core.dir_paths['BASEDIR'] + "/go"
        self.GOPATHDIR = self.prefab.core.dir_paths['BASEDIR'] + "/go_proj"
        self.GOPATH = self.GOPATHDIR  # backwards compatibility

    def isInstalled(self):
        rc, out, err = self.prefab.core.run(
            "go version", die=False, showout=False, profile=True)
        if rc==0 and self.doneGet("install") == True:
            if any(x in out for x in ['1.10.3','1.8.7']):
                return True
        return False

    def install(self, reset=False, old=False):
        if reset is False and self.isInstalled():
            return
        if self.prefab.core.isMac:
            if old is False:
                downl = "https://dl.google.com/go/go1.10.3.darwin-amd64.tar.gz"
            else:
                downl = "https://dl.google.com/go/go1.8.7.darwin-amd64.tar.gz"
        elif "ubuntu" in self.prefab.platformtype.platformtypes:
            if old is False:
                downl = "https://storage.googleapis.com/golang/go1.11.1.linux-amd64.tar.gz"
            else:
                downl = "https://dl.google.com/go/go1.8.7.linux-amd64.tar.gz"
        else:
            raise j.exceptions.RuntimeError("platform not supported")

        self.prefab.core.run(cmd=self.replace("rm -rf $GOROOTDIR"), die=True)
        self.prefab.core.dir_ensure(self.GOROOTDIR)
        self.prefab.core.dir_ensure(self.GOPATHDIR)

        profile = self.prefab.bash.profileDefault
        profile.envSet("GOROOT", self.GOROOTDIR)
        profile.envSet("GOPATH", self.GOPATHDIR)
        profile.addPath(self.prefab.core.joinpaths(self.GOPATHDIR, 'bin'))
        profile.addPath(self.prefab.core.joinpaths(self.GOROOTDIR, 'bin'))
        profile.save()

        self.prefab.core.file_download(downl, self.GOROOTDIR, overwrite=False, retry=3,
                                       timeout=0, expand=True, removeTopDir=True)

        self.prefab.core.dir_ensure("%s/src" % self.GOPATHDIR)
        self.prefab.core.dir_ensure("%s/pkg" % self.GOPATHDIR)
        self.prefab.core.dir_ensure("%s/bin" % self.GOPATHDIR)

        self.get("github.com/tools/godep")
        self.doneSet("install")

    def goraml(self, reset=False):
        """
        Install (using go get) goraml.
        """
        if reset is False and self.doneGet('goraml'):
            return

        self.install()
        self.bindata(reset=reset)

        C = '''
        go get -u github.com/tools/godep
        go get -u github.com/jteeuwen/go-bindata/...
        go get -u github.com/Jumpscale/go-raml
        set -ex
        cd $GOPATH/src/github.com/Jumpscale/go-raml
        sh build.sh
        '''
        self.prefab.core.execute_bash(C, profile=True)
        self.doneSet('goraml')

    def bindata(self, reset=False):
        """
        Install (using go get) go-bindata.
        """
        if reset is False and self.doneGet('bindata'):
            return
        C = '''
        set -ex
        go get -u github.com/jteeuwen/go-bindata/...
        cd $GOPATH/src/github.com/jteeuwen/go-bindata/go-bindata
        go build
        go install
        '''
        self.prefab.core.execute_bash(C, profile=True)
        self.doneSet('bindata')

    def glide(self):
        """
        install glide
        """
        if self.doneGet('glide'):
            return
        self.prefab.core.file_download(
            'https://glide.sh/get', '$TMPDIR/installglide.sh', minsizekb=4)
        self.prefab.core.run('. $TMPDIR/installglide.sh', profile=True)
        self.doneSet('glide')

    def clean_src_path(self):
        srcpath = self.prefab.core.joinpaths(self.GOPATHDIR, 'src')
        self.prefab.core.dir_remove(srcpath)

    def get(self, url, install=True, update=True, die=True):
        """
        @param url ,, str url to run the go get command on.
        @param install ,, bool will default build and install the repo if false will only get the repo.
        @param update ,, bool will if True will update requirements if they exist.
        e.g. url=github.com/tools/godep
        """
        self.clean_src_path()
        download_flag = ''
        update_flag = ''
        if not install:
            download_flag = '-d'
        if update:
            update_flag = '-u'
        self.prefab.core.run('go get %s -v %s %s' % (download_flag, update_flag, url),
                             profile=True, die=die)

    def godep(self, url, branch=None, depth=1):
        """
        @param url ,, str url to run the godep command on.
        @param branch ,,str branch to use on the specified repo
        @param depth ,,int depth of repo pull defines how shallow the git clone is
        e.g. url=github.com/tools/godep
        """
        self.clean_src_path()
        GOPATH = self.GOPATH

        pullurl = "git@%s.git" % url.replace('/', ':', 1)

        dest = self.prefab.tools.git.pullRepo(pullurl,
                                              branch=branch,
                                              depth=depth,
                                              dest='%s/src/%s' % (GOPATH, url),
                                              ssh=False)
        self.prefab.core.run('cd %s && godep restore' % dest, profile=True)
