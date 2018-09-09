from Jumpscale import j
import os
import textwrap

app = j.tools.prefab._getBaseAppClass()


class PrefabMicroEditor(app):
    NAME = "micro"

    def install(self, reset=False):
        """
        """

        if self.doneCheck("install", reset):
            return

        print("INSTALL MICROEDITOR")

        if self.core.isMac:
            url = "https://github.com/zyedidia/micro/releases/download/v1.3.3/micro-1.3.3-osx.tar.gz"
        elif self.core.isUbuntu:
            url = "https://github.com/zyedidia/micro/releases/download/v1.3.3/micro-1.3.3-linux64.tar.gz"
        else:
            raise RuntimeError("not implemented for other platforms")

        dest = self.prefab.network.tools.download(
            url=url, to='$TMPDIR/micro/', overwrite=False, retry=3, expand=True, removeTopDir=True)
        self.core.file_move("$TMPDIR/micro/micro",
                            "/usr/local/bin/micro", recursive=False)

        self.doneSet('install')
