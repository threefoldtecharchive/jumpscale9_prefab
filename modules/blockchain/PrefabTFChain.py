from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabTFChain(app):
    NAME = "tfchain"

    def build(self, branch=None,tag=None, revision=None, reset=False):
        if self.doneGet('build') and reset is False:
            return
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install("git")
        golang = self.prefab.runtimes.golang
        golang.install()
        GOPATH = golang.GOPATH
        url = 'github.com/threefoldfoundation'
        path = '%s/src/%s/tfchain' % (GOPATH, url)
        pullurl = 'https://%s/tfchain.git' % url
        dest = self.prefab.tools.git.pullRepo(pullurl,
                                              branch=branch,
                                              tag=tag,
                                              revision=revision,
                                              dest=path,
                                              ssh=False)
        cmd = 'cd {} && make install-std'.format(dest)
        self.prefab.core.run(cmd)

        self.doneSet('build')

    def install(self, branch=None,tag=None, revision=None, reset=False):
        # if branch, tag, revision = None it will build form master
        if self.doneGet('install') and reset is False:
            return

        self.build(branch=branch,tag=tag, revision=revision, reset=reset)
        tfchaindpath = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'tfchaind')
        tfchaincpath = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'tfchainc')

        self.prefab.core.file_copy(tfchaindpath, "$BINDIR/")
        self.prefab.core.file_copy(tfchaincpath, "$BINDIR/")

        self.doneSet('install')
