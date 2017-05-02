from js9 import j


app = j.tools.prefab._getBaseAppClass()


class CuisineInfluxdb(app):
    NAME = "influxd"

    def install(self, dependencies=False, start=False, reset=False):
        if reset is False and self.isInstalled():
            return

        if dependencies:
            self.prefab.package.mdupdate()

        self.prefab.core.dir_ensure('$BINDIR')

        if self.prefab.core.isMac:
            self.prefab.package.install('influxdb')
            self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/influxdb")
            self.prefab.core.file_copy("/usr/local/etc/influxdb.conf", "$TEMPLATEDIR/cfg/influxdb/influxdb.conf")

        elif self.prefab.core.isUbuntu:
            self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/influxdb")
            C = """
            set -ex
            cd $TMPDIR
            wget https://dl.influxdata.com/influxdb/releases/influxdb-0.13.0_linux_amd64.tar.gz
            tar xvfz influxdb-0.13.0_linux_amd64.tar.gz
            cp influxdb-0.13.0-1/usr/bin/influxd $BINDIR/influxd
            cp influxdb-0.13.0-1/etc/influxdb/influxdb.conf $TEMPLATEDIR/cfg/influxdb/influxdb.conf"""
            self.prefab.core.run(C, profile=True)
        else:
            raise RuntimeError("cannot install, unsuported platform")
        self.prefab.bash.profileJS.addPath(self.replace("$BINDIR"))
        self.prefab.bash.profileJS.save()
        binPath = self.prefab.bash.cmdGetPath('influxd')
        self.prefab.core.dir_ensure("$VARDIR/data/influxdb")
        self.prefab.core.dir_ensure("$VARDIR/data/influxdb/meta")
        self.prefab.core.dir_ensure("$VARDIR/data/influxdb/data")
        self.prefab.core.dir_ensure("$VARDIR/data/influxdb/wal")
        content = self.prefab.core.file_read('$TEMPLATEDIR/cfg/influxdb/influxdb.conf')
        cfg = j.data.serializer.toml.loads(content)
        cfg['meta']['dir'] = self.replace("$VARDIR/data/influxdb/meta")
        cfg['data']['dir'] = self.replace("$VARDIR/data/influxdb/data")
        cfg['data']['wal-dir'] = self.replace("$VARDIR/data/influxdb/wal")
        self.prefab.core.dir_ensure('$JSCFGDIR/influxdb')
        self.prefab.core.file_write('$JSCFGDIR/influxdb/influxdb.conf', j.data.serializer.toml.dumps(cfg))
        cmd = "%s -config $JSCFGDIR/influxdb/influxdb.conf" % (binPath)
        cmd = self.replace(cmd)
        self.prefab.core.file_write("$BINDIR/start_influxdb.sh", cmd, 777, replaceArgs=True)

        if start:
            self.start()

    def build(self, start=True):
        raise RuntimeError("not implemented")

    def start(self):
        binPath = self.prefab.bash.cmdGetPath('influxd')
        cmd = "%s -config $JSCFGDIR/influxdb/influxdb.conf" % (binPath)
        self.prefab.process.kill("influxdb")
        self.prefab.processmanager.ensure("influxdb", cmd=cmd, env={}, path="")
