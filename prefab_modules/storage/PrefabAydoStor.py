from Jumpscale import j


app = j.tools.prefab._BaseAppClass

# TODO: is this still correct, maybe our docker approach better, need to check


class PrefabAydoStor(app):

    NAME = 'stor'

    def build(self, addr='0.0.0.0:8090', backend="{DIR_VAR}/aydostor", start=True, install=True, reset=False):
        """
        Build and Install aydostore
        @input addr, address and port on which the service need to listen. e.g. : 0.0.0.0:8090
        @input backend, directory where to save the data push to the store
        """
        if self.isInstalled() and not reset:
            self._logger.info('Aydostor is already installed, pass reinstall=True parameter to reinstall')
            return

        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install('build-essential')

        self.prefab.core.dir_remove("%s/src" % self.prefab.bash.envGet('GOPATH'))
        self.prefab.runtimes.golang.get("github.com/g8os/stor")

        if install:
            self.install(addr, backend, start)

    def install(self, addr='0.0.0.0:8090', backend="{DIR_VAR}/aydostor", start=True):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        self.prefab.core.dir_ensure('{DIR_BIN}')
        self.prefab.core.file_copy(self.prefab.core.joinpaths(
            self.prefab.core.dir_paths['GODIR'], 'bin', 'stor'), '{DIR_BIN}', overwrite=True)
        self.prefab.bash.addPath("{DIR_BASE}/bin")

        pm = self.prefab.system.processmanager.get()
        pm.stop("stor")  # will also kill

        self.prefab.core.dir_ensure("{DIR_BASE}/cfg/stor")
        backend = self.executor.replace(backend)
        self.prefab.core.dir_ensure(backend)
        config = {
            'listen_addr': addr,
            'store_root': backend,
        }
        content = j.data.serializers.toml.dumps(config)
        self.prefab.core.dir_ensure('$TEMPLATEDIR/cfg/stor', recursive=True)
        self.prefab.core.file_write("$TEMPLATEDIR/cfg/stor/config.toml", content)

        if start:
            self.start(addr)

    def start(self, addr):
        res = addr.split(":")
        if len(res) == 2:
            addr, port = res[0], res[1]
        else:
            addr, port = res[0], '8090'

            self.prefab.ufw.allowIncoming(port)
            if self.prefab.system.process.tcpport_check(port, ""):
                raise RuntimeError(
                    "port %d is occupied, cannot start stor" % port)

        self.prefab.core.dir_ensure("{DIR_BASE}/cfg/stor/", recursive=True)
        self.prefab.core.file_copy("$TEMPLATEDIR/cfg/stor/config.toml", "{DIR_BASE}/cfg/stor/")
        cmd = self.prefab.bash.cmdGetPath("stor")
        pm = self.prefab.system.processmanager.get()
        pm.ensure("stor", '%s --config {DIR_BASE}/cfg/stor/config.toml' % cmd)
