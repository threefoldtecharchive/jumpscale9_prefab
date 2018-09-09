from Jumpscale import j


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
            rm -rf atomicswap
            git clone https://github.com/ahussein/atomicswap.git
        """
        self.core.run(cmds)
        self.doneSet('build')

    def install(self, reset=False):
        self.build(reset=reset)
        cmds = """
            cp $TMPDIR/atomicswap/cmd/btcatomicswap/btcatomicswap $BINDIR/
        """
        self.core.run(cmds)
        self.doneSet('install')
