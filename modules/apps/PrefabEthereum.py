from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabEthereum(app):
    NAME = "geth"

    def build(self, reset=False):
        """Build the binaries of ethereum
        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
        """

        if self.doneGet('build') and reset is False:
            return

        self.prefab.system.base.install(upgrade=True)
        self.prefab.runtimes.golang.install()
        self.doneSet('build')

    def install(self, reset=False):
        self.build()
        if self.doneGet('install') and reset is False:
            return
        self.prefab.system.package.install("build-essential")

        geth_path = "{}/src/github.com/ethereum/go-ethereum".format(self.prefab.runtimes.golang.GOPATHDIR)

        cmd = """
        go get github.com/ethereum/go-ethereum
        cd {geth_path}
        make geth
        cp build/bin/geth $BINDIR
        """.format(geth_path=geth_path)
        self.prefab.core.run(cmd)

        self.doneSet('install')
