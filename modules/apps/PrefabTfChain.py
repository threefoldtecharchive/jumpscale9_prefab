from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabTfChain(app):
    NAME = "tfchain"

    def build(self, reset=False):
        """Get/Build the binaries of tfchain (tfchaid and tfchainc)

        Keyword Arguments:
            reset {bool} -- reset the build process (default: {False})
        """
        self.prefab.blockchain.tfchain.build(reset=reset) 
    
    def install(self, reset=False):
        self.prefab.blockchain.tfchain.install(reset=reset) 