from Jumpscale import j


app = j.tools.prefab._BaseAppClass


class PrefabAtomicswap(app):
    NAME = "atomicswap"

    def build(self, branch=None,tag=None, revision=None, reset=False):
        if self.doneGet('build') and reset is False:
            return
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install("git")
        golang = self.prefab.runtimes.golang
        golang.install()
        GOPATH = golang.GOPATH
        url = 'github.com/rivine'
        path = '%s/src/%s/atomicswap' % (GOPATH, url)
        pullurl = 'https://%s/atomicswap.git' % url
        dest = self.prefab.tools.git.pullRepo(pullurl,
                                              branch=branch,
                                              tag=tag,
                                              revision=revision,
                                              dest=path,
                                              ssh=False)
        cmd = 'cd {} && make install'.format(dest)
        self.prefab.core.run(cmd)

        self.doneSet('build')

    def install(self, branch=None,tag='v0.1.0', revision=None, reset=False):
        # if branch, tag, revision = None it will build form master
        if self.doneGet('install') and reset is False:
            return

        self.build(branch=branch,tag=tag, revision=revision, reset=reset)
        tfchaindpath = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'btcatomicswap')
        tfchaincpath = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'ethatomicswap')

        self.prefab.core.file_copy(tfchaindpath, "{DIR_BIN}/")
        self.prefab.core.file_copy(tfchaincpath, "{DIR_BIN}/")

        self.doneSet('install')
