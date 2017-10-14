from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabMariadb(app):
    NAME = 'mariadb'

    def install(self, start=False):
        if self.doneCheck("install", reset):
            return
        self.prefab.system.package.install("mariadb-server")
        self.prefab.core.dir_ensure("/data/db")
        self.prefab.core.dir_ensure("/var/run/mysqld")
        script = """
        chown -R mysql.mysql /data/db/
        chown -R mysql.mysql /var/run/mysqld
        mysql_install_db --basedir=/usr --datadir=/data/db
        """
        self.prefab.core.run(script)

        self.doneSet("install")

        if start:
            self.start()

    def start(self):
        cmd = "/usr/sbin/mysqld --basedir=/usr --datadir=/data/db \
                --plugin-dir=/usr/lib/mysql/plugin --log-error=/dev/log/mysql/error.log \
                --pid-file=/var/run/mysqld/mysqld.pid --socket=/var/run/mysqld/mysqld.sock --port=3306"
        self.prefab.core.run(cmd)
