from js9 import j
import os

app = j.tools.prefab._getBaseAppClass()


class PrefabNoVNC(app):
    NAME = "novnc"

    def install(self, reset=False, branch="0.5.1"):
        if reset is False and self.isInstalled():
            return

        if self.prefab.core.isUbuntu:
            self.prefab.development.git.pullRepo("https://github.com/gigforks/noVNC", branch=branch)
