from jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabInfluxdb(app):
    NAME = "influxd"

    def install(self, dependencies=False, start=False, reset=False):
        if self.doneCheck("install", reset):
            return

        if dependencies:
            self.prefab.system.package.mdupdate()

        self.prefab.core.dir_ensure('$BINDIR')

        if self.prefab.core.isMac:
            self.prefab.system.package.install('influxdb')
            self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/influxdb")
            self.prefab.core.file_copy(
                "/usr/local/etc/influxdb.conf", "$TEMPLATEDIR/cfg/influxdb/influxdb.conf")

        elif self.prefab.core.isUbuntu:
            self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/influxdb")
            C = """
            set -ex
            cd $TMPDIR
            wget https://dl.influxdata.com/influxdb/releases/influxdb-1.6.0-static_linux_amd64.tar.gz
            tar xvfz influxdb-1.6.0-static_linux_amd64.tar.gz
            cp influxdb-1.6.0-1/influxd $BINDIR/influxd
            cp influxdb-1.6.0-1/influx $BINDIR/influx
            cp influxdb-1.6.0-1/influx_inspect $BINDIR/influx_inspect
            cp influxdb-1.6.0-1/influx_stress $BINDIR/influx_stress
            cp influxdb-1.6.0-1/influx_tsm $BINDIR/influx_tsm
            cp influxdb-1.6.0-1/influxdb.conf $TEMPLATEDIR/cfg/influxdb/influxdb.conf"""
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
        content = self.prefab.core.file_read(
            '$TEMPLATEDIR/cfg/influxdb/influxdb.conf')
        cfg = j.data.serializers.toml.loads(content)
        cfg['meta']['dir'] = self.replace("$VARDIR/data/influxdb/meta")
        cfg['data']['dir'] = self.replace("$VARDIR/data/influxdb/data")
        cfg['data']['wal-dir'] = self.replace("$VARDIR/data/influxdb/wal")
        self.prefab.core.dir_ensure('$CFGDIR/influxdb')
        self.prefab.core.file_write('$CFGDIR/influxdb/influxdb.conf', j.data.serializers.toml.dumps(cfg))
        cmd = "%s -config $CFGDIR/influxdb/influxdb.conf" % (binPath)
        cmd = self.replace(cmd)
        self.prefab.core.file_write("$BINDIR/start_influxdb.sh", cmd, mode=0o777)

        if start:
            self.start()

    def build(self, start=True):
        raise RuntimeError("not implemented")

    def start(self):
        binPath = self.prefab.bash.cmdGetPath('influxd')
        cmd = "%s -config $CFGDIR/influxdb/influxdb.conf" % (binPath)
        self.prefab.system.process.kill("influxdb")
        pm = self.prefab.system.processmanager.get()
        pm.ensure("influxdb", cmd=cmd, env={}, path="")
