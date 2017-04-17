from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()

# TODO: is this still correct, maybe our docker approach better, need to check


class CuisineAydoStor(app):

    NAME = 'stor'

    def build(self, addr='0.0.0.0:8090', backend="$VARDIR/aydostor", start=True, install=True, reset=False):
        """
        Build and Install aydostore
        @input addr, address and port on which the service need to listen. e.g. : 0.0.0.0:8090
        @input backend, directory where to save the data push to the store
        """
        if self.isInstalled() and not reset:
            self.logger.info('Aydostor is already installed, pass reinstall=True parameter to reinstall')
            return

        self.cuisine.package.mdupdate()
        self.cuisine.package.install('build-essential')

        self.cuisine.core.dir_remove("%s/src" % self.cuisine.bash.envGet('GOPATH'))
        self.cuisine.development.golang.get("github.com/g8os/stor")

        if install:
            self.install(addr, backend, start)

    def install(self, addr='0.0.0.0:8090', backend="$VARDIR/aydostor", start=True):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        self.cuisine.core.dir_ensure('$BINDIR')
        self.cuisine.core.file_copy(self.cuisine.core.joinpaths(
            self.cuisine.core.dir_paths['GODIR'], 'bin', 'stor'), '$BINDIR', overwrite=True)
        self.cuisine.bash.addPath("$BASEDIR/bin")

        self.cuisine.processmanager.stop("stor")  # will also kill

        self.cuisine.core.dir_ensure("$JSCFGDIR/stor")
        backend = self.replace(backend)
        self.cuisine.core.dir_ensure(backend)
        config = {
            'listen_addr': addr,
            'store_root': backend,
        }
        content = j.data.serializer.toml.dumps(config)
        self.cuisine.core.dir_ensure('$TEMPLATEDIR/cfg/stor', recursive=True)
        self.cuisine.core.file_write("$TEMPLATEDIR/cfg/stor/config.toml", content)

        if start:
            self.start(addr)

    def start(self, addr):
        res = addr.split(":")
        if len(res) == 2:
            addr, port = res[0], res[1]
        else:
            addr, port = res[0], '8090'

            self.cuisine.ufw.allowIncoming(port)
            if self.cuisine.process.tcpport_check(port, ""):
                raise RuntimeError(
                    "port %d is occupied, cannot start stor" % port)

        self.cuisine.core.dir_ensure("$JSCFGDIR/stor/", recursive=True)
        self.cuisine.core.file_copy("$TEMPLATEDIR/cfg/stor/config.toml", "$JSCFGDIR/stor/")
        cmd = self.cuisine.bash.cmdGetPath("stor")
        self.cuisine.processmanager.ensure("stor", '%s --config $JSCFGDIR/stor/config.toml' % cmd)
