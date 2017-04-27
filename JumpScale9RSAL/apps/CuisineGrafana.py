from js9 import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineGrafana(app):

    NAME = 'grafana-server'

    def build(self, reset=False):

        if reset is False and self.isInstalled():
            return

        if self.cuisine.core.isUbuntu:
            C = """
            cd $TMPDIR
            wget https://grafanarel.s3.amazonaws.com/builds/grafana_3.1.1-1470047149_amd64.deb
            sudo apt-get install -y adduser libfontconfig
            sudo dpkg -i grafana_3.1.1-1470047149_amd64.deb

            """
            self.cuisine.core.run(C, profile=True)
        else:
            raise RuntimeError("platform not supported")

    def install(self, start=False, influx_addr='127.0.0.1', influx_port=8086, port=3000):
        self.cuisine.core.dir_ensure('$BINDIR')
        self.cuisine.core.file_copy("/usr/sbin/grafana*", dest="$BINDIR")

        self.cuisine.core.dir_ensure("$JSAPPSDIR/grafana")
        self.cuisine.core.file_copy("/usr/share/grafana/", "$JSAPPSDIR/", recursive=True)

        if self.cuisine.core.file_exists("/usr/share/grafana/conf/defaults.ini"):
            cfg = self.cuisine.core.file_read("/usr/share/grafana/conf/defaults.ini")
        else:
            cfg = self.cuisine.core.file_read('$TMPDIR/cfg/grafana/conf/defaults.ini')
        self.cuisine.core.file_write('$JSCFGDIR/grafana/grafana.ini', cfg)

        if start:
            self.start(influx_addr, influx_port, port)

    def start(self, influx_addr='127.0.0.1', influx_port=8086, port=3000):

        cmd = "$BINDIR/grafana-server --config=$JSCFGDIR/grafana/grafana.ini\n"
        cmd = self.replace(cmd)
        self.cuisine.core.file_write("/opt/jumpscale9/bin/start_grafana.sh", cmd, 777, replaceArgs=True)
        self.cuisine.process.kill("grafana-server")
        self.cuisine.processmanager.ensure("grafana-server", cmd=cmd, env={}, path='$JSAPPSDIR/grafana')
        grafanaclient = j.clients.grafana.get(
            url='http://%s:%d' % (self.cuisine.core.executor.addr, port), username='admin', password='admin')
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
