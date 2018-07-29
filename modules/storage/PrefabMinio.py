from jumpscale import j
import os
import textwrap

app = j.tools.prefab._getBaseAppClass()

class PrefabMinio(app):
    NAME = "minio"

    def _init(self):
        self.BUILDDIR = self.replace("$TMPDIR/minio")

    def build(self, reset=False, install=False):
        """
        Builds minio

        @param reset boolean: forces the build operation.
        """
        if self.doneCheck("build", reset):
            return
        self.prefab.core.dir_ensure(self.BUILDDIR)

        minio_url = "https://dl.minio.io/server/minio/release/linux-amd64/minio"
        self.prefab.core.file_download(minio_url, overwrite=True, to=self.BUILDDIR, expand=False, removeTopDir=True)
        self.doneSet('build')

        if install:
            self.install(False)

    def install(self, reset=False, start=False):
        """
        Installs minio

        @param reset boolean: forces the install operation.
        """
        if self.doneCheck("install", reset):
            return
        self.prefab.core.run("cp $TMPDIR/minio $BINDIR/")
        self.doneSet('install')

        if start:
            self.start()

    def start(self, name="main", datadir="/tmp/shared", address="0.0.0.0", port=90000, miniokey="", miniosecret=""):
        """
        Starts minio.
        """
        self.prefab.core.dir_ensure(datadir)

        cmd = "MINIO_ACCESS_KEY={} MINIO_SECRET_KEY={} minio server --address {}:{} {}".format(miniokey, miniosecret, address, port, datadir)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='minio_{}'.format(name), cmd=cmd)


    def stop(self, name='main'):
        """
        Stops minio 
        """

        pm.stop(name='minio_{}'.format(name))


    def restart(self, name="main"):
        self.stop(name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        pass

