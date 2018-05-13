"""
Prefab module to build/install bitcoin daemon and client
mrCkmU5BfygP6zmLLEQfcWjph2pZ3HGZ9j
"""

from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabBitcoin(base):
    """
    Prefab Bitcoin class
    """

    def install(self, reset=False):
        """
        Install Bitcoin daemon and cli

        @param reset: If True, installation steps will be re-done if already installed.
        """
        if not reset and self.doneCheck('install'):
            # already installed
            return

        self.prefab.bash.locale_check()
        if self.prefab.core.isUbuntu:
            self.prefab.system.package.mdupdate(reset=True)
            self.prefab.system.package.install("build-essential libtool autotools-dev autoconf libssl-dev libboost-all-dev software-properties-common git")
            self.prefab.system.package._repository_ensure_apt("ppa:bitcoin/bitcoin")
            self.prefab.system.package._repository_ensure_apt("ppa:longsleep/golang-backports")
            self.prefab.system.package.mdupdate(reset=True)
            self.prefab.system.package.install("golang-go")
            self.prefab.system.package.install("bitcoind")
        else:
            raise RuntimeError("Unsported platform")

        self.doneSet("install")
