from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabGrafana(app):

    NAME = 'grafana-server'

    def build(self, reset=False):

        if reset is False and self.isInstalled():
            return

        if self.prefab.core.isUbuntu:
            C = """
            cd $TMPDIR
            wget https://grafanarel.s3.amazonaws.com/builds/grafana_3.1.1-1470047149_amd64.deb
            sudo apt-get install -y adduser libfontconfig
            sudo dpkg -i grafana_3.1.1-1470047149_amd64.deb

            """
            self.prefab.core.run(C, profile=True)
        else:
            raise RuntimeError("platform not supported")

    def install(self, start=False, influx_addr='127.0.0.1', influx_port=8086, port=3000):
        self.prefab.core.dir_ensure('$BINDIR')
        self.prefab.core.file_copy("/usr/sbin/grafana*", dest="$BINDIR")

        self.prefab.core.dir_ensure("$JSAPPSDIR/grafana")
        self.prefab.core.file_copy("/usr/share/grafana/", "$JSAPPSDIR/", recursive=True)

        if self.prefab.core.file_exists("/usr/share/grafana/conf/defaults.ini"):
            cfg = self.prefab.core.file_read("/usr/share/grafana/conf/defaults.ini")
        else:
            cfg = self.prefab.core.file_read('$TMPDIR/cfg/grafana/conf/defaults.ini')
        self.prefab.core.file_write('$JSCFGDIR/grafana/grafana.ini', cfg)

        if start:
            self.start(influx_addr, influx_port, port)

    def start(self, influx_addr='127.0.0.1', influx_port=8086, port=3000):

        cmd = "$BINDIR/grafana-server --config=$JSCFGDIR/grafana/grafana.ini\n"
        cmd = self.replace(cmd)
        self.prefab.core.file_write("/opt/jumpscale9/bin/start_grafana.sh", cmd, 777, replaceArgs=True)
        self.prefab.system.process.kill("grafana-server")
        pm = self.prefab.system.processmanager.get()
        pm.ensure("grafana-server", cmd=cmd, env={}, path='$JSAPPSDIR/grafana')
        grafanaclient = j.clients.grafana.get(
            url='http://%s:%d' % (self.prefab.core.executor.addr, port), username='admin', password='admin')
        data = {
            'type': 'influxdb',
            'access': 'proxy',
            'database': 'statistics',
            'name': 'influxdb_main',
            'url': 'http://%s:%u' % (influx_addr, influx_port),
            'user': 'admin',
            'password': 'passwd',
            'default': True,
        }
        import time
        import requests
        now = time.time()
        while time.time() - now < 10:
            try:
                grafanaclient.addDataSource(data)
                if not grafanaclient.listDataSources():
                    continue
                break
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                pass
