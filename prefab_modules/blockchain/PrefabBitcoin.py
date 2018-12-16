from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabBitcoin(app):
    NAME = "bitcoind"

    def _init(self):
        self.BITCOIN_64BIT_URL = "https://bitcoin.org/bin/bitcoin-core-0.16.0/bitcoin-0.16.0-x86_64-linux-gnu.tar.gz"
        self.DOWNLOAD_DEST = self.executor.replace("{DIR_VAR}/build/bitcoin-0.16.0.tar.gz")
        self.EXTRACTED_FILEPATH = self.executor.replace("{DIR_TEMP}/bitcoin-0.16.0")


    def build(self, reset=False):
        """Get/Build the binaries of bitcoin
        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
        """

        if self.doneGet('build') and reset is False:
            return

        if not self.prefab.core.file_exists(self.DOWNLOAD_DEST):
            self.prefab.core.file_download(self.BITCOIN_64BIT_URL, self.DOWNLOAD_DEST)

        self.prefab.core.file_expand(self.DOWNLOAD_DEST, "{DIR_TEMP}")

        self.doneSet('build')


    def install(self, reset=False):
        """
        Install the bitcoind binaries
        """

        if self.doneGet('install') and reset is False:
            return

        self.build(reset=reset)

        cmd = self.executor.replace('cp {}/bin/* {DIR_BIN}/'.format(self.EXTRACTED_FILEPATH))
        self.prefab.core.run(cmd)

        cmd = self.executor.replace('cp {}/lib/* $LIBDIR/'.format(self.EXTRACTED_FILEPATH))
        self.prefab.core.run(cmd)

        self.doneSet('install')
