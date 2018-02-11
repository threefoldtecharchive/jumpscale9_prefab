from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabMariadb(app):
    NAME = 'mariadb'

    def install(self, start=False, reset=False):
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

    def db_export(self, dbname):
        raise RuntimeError()

    def db_import(self, dbname, sqlfile):
        raise RuntimeError()

    def db_init(self):
        raise RuntimeError()

    def admin_create(self, username):
        """
        creates user with all rights
        """
        raise RuntimeError()

    def user_create(self, username):
        """
        creates user with no rights
        """
        raise RuntimeError()

    def user_db_access(self, username, dbname):
        """
        give use right to this database (fully)
        """
        raise RuntimeError()

    def sql_execute(self, dbname, sql):
        raise RuntimeError()
