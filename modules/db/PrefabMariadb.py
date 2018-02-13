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
            try:
                self.start()
            except Exception:
                j.logger.get().warning("MySql didn't started, maybe it's "
                        "already running or the port 3306 is used by other service")

    def start(self):
        cmd = "/usr/sbin/mysqld --basedir=/usr --datadir=/data/db \
                --plugin-dir=/usr/lib/mysql/plugin --log-error=/dev/log/mysql/error.log \
                --pid-file=/var/run/mysqld/mysqld.pid --socket=/var/run/mysqld/mysqld.sock --port=3306"
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='mysqlserver', cmd=cmd)
        

    def db_export(self, dbname):
        raise RuntimeError()

    def db_import(self, dbname, sqlfile):
        raise RuntimeError()

    def db_init(self):
        raise RuntimeError()

    def admin_create(self, username, password, root_name='root', root_password='', db_name = '*'):
        """
        creates user with all rights
        @param username: (required) username of the user that will be created
        @param password: (required) password of the user that will be created
        @param root_name: the root user username that will be user to create the new user
        @param root_password: the root user password that will be used to creat the new user
        """
        # if root_password is non will add -p --password before the password to allow password  
        if root_password:
            root_password = "-p --password=" + root_password
        cmd = """
            mysql -u {root_name} {root_password} -e "GRANT ALL PRIVILEGES ON {db_name}.* TO '{username}'@'localhost' IDENTIFIED BY '{password}';"
        """.format(root_name= root_name, root_password=root_password, 
                    username=username, password=password, db_name=db_name)
        
        self.prefab.executor.execute(cmd)

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

    def sql_execute(self, sql, username='root', password='', dbname=''):
        if password:
            password = "-p --password=" + password

        if dbname:
            dbname = "USE %s;" % dbname
        
        prefix = "mysql -u %s %s -e" % (username, password)
        sql = '%s "%s %s"' % (prefix, dbname, sql)
        self.prefab.executor.execute(sql)
