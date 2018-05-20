from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabAtomicswap(app):
    NAME = "btcatomicswap"

    def build(self, reset=False):
        """Get/Build the binaries of AtomicExchange
        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
        """

        if self.doneGet('build') and reset is False:
            return

        cmds = """
            cd $TMPDIR
            git clone https://github.com/JimberSoftware/AtomicExchange
        """
        self.core.run(cmds)
        self.doneSet('build')

    def install(self):
        cmds = """
            cp $TMPDIR/AtomicExchange/cryptoDocker/btcatomicswap $BINDIR/
        """
        self.core.run(cmds)
        self.doneSet('install')