from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineInfluxdb(app):
    NAME = "influxd"

    def install(self, dependencies=False, start=False, reset=False):
        if reset is False and self.isInstalled():
            return

        if dependencies:
            self.cuisine.package.mdupdate()

        self.cuisine.core.dir_ensure('$BINDIR')

        if self.cuisine.core.isMac:
            self.cuisine.package.install('influxdb')
            self.cuisine.core.dir_ensure("$TEMPLATEDIR/cfg/influxdb")
            self.cuisine.core.file_copy("/usr/local/etc/influxdb.conf", "$TEMPLATEDIR/cfg/influxdb/influxdb.conf")

        elif self.cuisine.core.isUbuntu:
            self.cuisine.core.dir_ensure("$TEMPLATEDIR/cfg/influxdb")
            C = """
            set -ex
            cd $TMPDIR
            wget https://dl.influxdata.com/influxdb/releases/influxdb-0.13.0_linux_amd64.tar.gz
            tar xvfz influxdb-0.13.0_linux_amd64.tar.gz
            cp influxdb-0.13.0-1/usr/bin/influxd $BINDIR/influxd
            cp influxdb-0.13.0-1/etc/influxdb/influxdb.conf $TEMPLATEDIR/cfg/influxdb/influxdb.conf"""
            self.cuisine.core.run(C, profile=True)
        else:
            raise RuntimeError("cannot install, unsuported platform")
        self.cuisine.bash.profileJS.addPath(self.replace("$BINDIR"))
        self.cuisine.bash.profileJS.save()
        binPath = self.cuisine.bash.cmdGetPath('influxd')
        self.cuisine.core.dir_ensure("$VARDIR/data/influxdb")
        self.cuisine.core.dir_ensure("$VARDIR/data/influxdb/meta")
        self.cuisine.core.dir_ensure("$VARDIR/data/influxdb/data")
        self.cuisine.core.dir_ensure("$VARDIR/data/influxdb/wal")
        content = self.cuisine.core.file_read('$TEMPLATEDIR/cfg/influxdb/influxdb.conf')
        cfg = j.data.serializer.toml.loads(content)
        cfg['meta']['dir'] = self.replace("$VARDIR/data/influxdb/meta")
        cfg['data']['dir'] = self.replace("$VARDIR/data/influxdb/data")
        cfg['data']['wal-dir'] = self.replace("$VARDIR/data/influxdb/wal")
        self.cuisine.core.dir_ensure('$JSCFGDIR/influxdb')
        self.cuisine.core.file_write('$JSCFGDIR/influxdb/influxdb.conf', j.data.serializer.toml.dumps(cfg))
        cmd = "%s -config $JSCFGDIR/influxdb/influxdb.conf" % (binPath)
        cmd = self.replace(cmd)
        self.cuisine.core.file_write("$BINDIR/start_influxdb.sh", cmd, 777, replaceArgs=True)

        if start:
            self.start()

    def build(self, start=True):
        raise RuntimeError("not implemented")

    def start(self):
        binPath = self.cuisine.bash.cmdGetPath('influxd')
        cmd = "%s -config $JSCFGDIR/influxdb/influxdb.conf" % (binPath)
        self.cuisine.process.kill("influxdb")
        self.cuisine.processmanager.ensure("influxdb", cmd=cmd, env={}, path="")
