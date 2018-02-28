from js9 import j
import os
import textwrap

app = j.tools.prefab._getBaseAppClass()

class PrefabDuplicacy(app):
    NAME = "duplicacy"

    def _init(self):
        self.BUILDDIR = self.replace("$TMPDIR/duplicacy")

    def build(self, reset=False, install=False):
        """
        Builds duplicacy

        @param reset boolean: forces the build operation.
        """
        if self.doneCheck("build", reset):
            return
        self.prefab.core.dir_ensure(self.BUILDDIR)

        dup_url = "https://github.com/gilbertchen/duplicacy/releases/download/v2.0.10/duplicacy_linux_x64_2.0.10"
        self.prefab.core.file_download(dup_url, overwrite=True, to=self.BUILDDIR, expand=False, removeTopDir=True)
        self.doneSet('build')

        if install:
            self.install(False)

    def install(self, reset=False, start=False):
        """
        Installs duplicacy

        @param reset boolean: forces the install operation.
        """
        if self.doneCheck("install", reset):
            return
        self.prefab.core.run("cp $TMPDIR/duplicacy_linux_x64_2.0.10 $BINDIR/duplicacy")
        self.doneSet('install')

        if start:
            self.start()

    def start(self, name="main"):
        """
        Starts duplicacy.
        """
        pass


    def stop(self, name='main'):
        """
        Stops duplicacy 
        """

        pass

    def restart(self, name="main"):
        self.stop(name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        pass

