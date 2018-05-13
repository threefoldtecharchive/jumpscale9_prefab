"""
Prefab module to build/install tfchain daemon and client
"""

from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabTFChain(base):
    """
    Prefab TFChain class
    """

    def install(self, reset=False):
        """
        Install TFChain daemon and cli

        @param reset: If True, installation steps will be re-done if already installed.
        """
        if not reset and self.doneCheck('install'):
            # already installed
            return

        self.prefab.bash.locale_check()
        if self.prefab.core.isUbuntu:
            self.prefab.apps.tfchain.build(reset=reset)
        else:
            raise RuntimeError("Unsported platform")

        self.doneSet("install")
