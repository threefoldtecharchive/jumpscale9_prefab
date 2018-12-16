from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabCockroachDB(app):
    NAME = 'cockroachdb'

    def install(self, start=True, reset=False):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        if self.doneCheck("install", reset):
            return

        appbase = "%s/" % self.prefab.core.dir_paths["BINDIR"]
        self.prefab.core.dir_ensure(appbase)

        url = 'https://binaries.cockroachdb.com/cockroach-latest.linux-amd64.tgz'
        dest = "{DIR_TEMP}/cockroach-latest.linux-amd64"

        self.logger.info('Downloading CockroachDB.')
        self.prefab.core.file_download(
            url, to="{DIR_TEMP}", overwrite=False, expand=True)
        tarpaths = self.prefab.core.find(
            "{DIR_TEMP}", recursive=False, pattern="*cockroach*.tgz", type='f')
        if len(tarpaths) == 0:
            raise j.exceptions.Input(message="could not download:%s, did not find in %s" % (url, self.executor.replace("{DIR_TEMP}")))
        tarpath = tarpaths[0]
        self.prefab.core.file_expand(tarpath, "{DIR_TEMP}")

        for file in self.prefab.core.find(dest, type='f'):
            self.prefab.core.file_copy(file, appbase)
        self.doneSet("install")
        if start:
            self.start(reset=reset)

    def build(self, start=True, reset=False):
        raise RuntimeError("not implemented")

    def start(self, host="localhost", insecure=True, background=False, reset=False, port=26257, http_port=8581):
        if self.isStarted() and not reset:
            return
        cmd = "{DIR_BIN}/cockroach start --host=%s" % host
        if insecure:
            cmd = "%s --insecure" % (cmd)
        if background:
            cmd = "%s --background" % (cmd)
        cmd = "%s --port=%s --http-port=%s" % (cmd, port, http_port)

        # cmd = "{DIR_BIN}/cockroach start --insecure --host=localhost --background"
        self.prefab.system.process.kill("cockroach")
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="cockroach", cmd=cmd, env={}, path="", autostart=True)

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("cockroach")
