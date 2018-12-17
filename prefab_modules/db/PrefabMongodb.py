from Jumpscale import j
from time import sleep


app = j.tools.prefab._getBaseAppClass()


class PrefabMongodb(app):
    NAME = 'mongod'

    def install(self, start=True, reset=False):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        if self.doneCheck("install", reset):
            return

        if self.prefab.core.isMac:
            self.prefab.core.run("brew uninstall mongodb", die=False)

        appbase = "%s/" % self.prefab.core.dir_paths["BINDIR"]
        self.prefab.core.dir_ensure(appbase)

        url = None
        if self.prefab.core.isUbuntu:
            url = 'https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1604-3.4.0.tgz'
            dest = "{DIR_TEMP}/mongodb-linux-x86_64-ubuntu1604-3.4.0/bin/"
        elif self.prefab.core.isArch:
            self.prefab.system.package.install("mongodb")
        elif self.prefab.core.isMac:
            url = 'https://fastdl.mongodb.org/osx/mongodb-osx-ssl-x86_64-3.4.0.tgz'
            dest = "{DIR_TEMP}/mongodb-osx-x86_64-3.4.0/bin/"
        else:
            raise j.exceptions.RuntimeError("unsupported platform")

        if url:
            self._logger.info('Downloading mongodb.')
            self.prefab.core.file_download(
                url, to="{DIR_TEMP}", overwrite=False, expand=True)
            tarpaths = self.prefab.core.find(
                "{DIR_TEMP}", recursive=False, pattern="*mongodb*.tgz", type='f')
            if len(tarpaths) == 0:
                raise j.exceptions.Input(message="could not download:%s, did not find in %s" % (url, self.executor.replace("{DIR_TEMP}")))
            tarpath = tarpaths[0]
            self.prefab.core.file_expand(tarpath, "{DIR_TEMP}")

            for file in self.prefab.core.find(dest, type='f'):
                self.prefab.core.file_copy(file, appbase)

        self.prefab.core.dir_ensure('{DIR_VAR}/data/mongodb')
        self.doneSet("install")
        if start:
            self.start(reset=reset)

    def build(self, start=True, reset=False):
        raise RuntimeError("not implemented")

    def start(self, reset=False):
        if self.isStarted() and not reset:
            return
        self.prefab.core.dir_ensure('{DIR_VAR}/data/mongodb')
        cmd = "mongod --dbpath '{DIR_VAR}/data/mongodb'"
        self.prefab.system.process.kill("mongod")
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="mongod", cmd=cmd, env={}, path="", autostart=True)

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("mongod")
