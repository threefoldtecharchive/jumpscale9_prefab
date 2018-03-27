from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabTfChain(app):
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

        cmd = 'cd {} && go build -ldflags "-linkmode external -extldflags -static" -o ../../bin/{}'
        self.prefab.core.execute_bash(cmd.format(
            self.prefab.core.joinpaths(dir_location, 'tfchaind'), 'tfchaind'))
        self.prefab.core.execute_bash(cmd.format(
            self.prefab.core.joinpaths(dir_location, 'tfchainc'), 'tfchainc'))

        self.doneSet('build')
