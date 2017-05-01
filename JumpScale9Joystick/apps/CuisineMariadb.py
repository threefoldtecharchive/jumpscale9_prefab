from js9 import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineMariadb(app):
    NAME = 'mariadb'

    def install(self, start=False):
        self.cuisine.package.install("mariadb-server")
        self.cuisine.core.dir_ensure("/data/db")
        self.cuisine.core.dir_ensure("/var/run/mysqld")
        script = """
        chown -R mysql.mysql /data/db/
        chown -R mysql.mysql /var/run/mysqld
        mysql_install_db --basedir=/usr --datadir=/data/db
        """
        self.cuisine.core.run(script)
        if start:
            self.start()

    def start(self):
        cmd = "/usr/sbin/mysqld --basedir=/usr --datadir=/data/db \
                --plugin-dir=/usr/lib/mysql/plugin --log-error=/dev/log/mysql/error.log \
                --pid-file=/var/run/mysqld/mysqld.pid --socket=/var/run/mysqld/mysqld.sock --port=3306"
        self.cuisine.core.run(cmd)
