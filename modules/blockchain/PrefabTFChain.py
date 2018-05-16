from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabTFChain(app):
    NAME = "tfchain"

    def build(self, reset=False):
        """Get/Build the binaries of tfchain (tfchaid and tfchainc)

        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
        """

        if self.doneGet('build') and reset is False:
            return

        golang = self.prefab.runtimes.golang
        golang.install()

        dir_location = 'github.com/threefoldfoundation/tfchain'
        self.prefab.runtimes.golang.get(dir_location, die=False)
        dir_location = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH,
                                                  'src',
                                                  dir_location, 'cmd')

        cmd = 'cd {} && go build -ldflags "-linkmode external -extldflags -static" -o {}'
        self.prefab.core.run(cmd.format(
            self.prefab.core.joinpaths(dir_location, 'tfchaind'),
            j.sal.fs.joinPaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'tfchaind')), profile=True)
        self.prefab.core.run(cmd.format(
            self.prefab.core.joinpaths(dir_location, 'tfchainc'),
            j.sal.fs.joinPaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'tfchainc')), profile=True)

        self.doneSet('build')
    
    def install(self, reset=False):
        if self.doneGet('install') and reset is False:
            return
        
        tfchaindpath = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'tfchaind')
        tfchaincpath = self.prefab.core.joinpaths(self.prefab.runtimes.golang.GOPATH, 'bin', 'tfchainc') 

        self.prefab.core.file_copy(tfchaindpath, "$BINDIR/")
        self.prefab.core.file_copy(tfchaincpath, "$BINDIR/")

        self.doneSet('install')
