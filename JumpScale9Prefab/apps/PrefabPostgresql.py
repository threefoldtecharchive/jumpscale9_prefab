from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabPostgresql(app):
    NAME = "psql"

    def _init(self):
        self.BUILD_DIR = '$TMPDIR/postgresql'
        self.passwd = "postgres"
        self.dbdir = "$VARDIR/postgresqldb"

    def build(self, beta=False):
        """
        beta is 2 for 10 release
        """
        if self.doneGet('build') or self.isInstalled():
            return
        if beta:
            postgres_url = 'https://ftp.postgresql.org/pub/source/v10beta2/postgresql-10beta3.tar.bz2'
        else:
            postgres_url = 'https://ftp.postgresql.org/pub/source/v9.6.3/postgresql-9.6.3.tar.gz'
        self.prefab.core.file_download(
            postgres_url, overwrite=False, to=self.BUILD_DIR, expand=True, removeTopDir=True)
        self.prefab.core.dir_ensure("$JSAPPSDIR/pgsql")
        self.prefab.core.dir_ensure("$BINDIR")
        self.prefab.core.dir_ensure("$LIBDIR/postgres")
        self.prefab.package.multiInstall(
            ['build-essential', 'zlib1g-dev', 'libreadline-dev'])
        cmd = """
        cd {}
        ./configure --prefix=$JSAPPSDIR/pgsql --bindir=$BINDIR --sysconfdir=$CFGDIR --libdir=$LIBDIR/postgres --datarootdir=$JSAPPSDIR/pgsql/share
        make
        """.format(self.BUILD_DIR)
        self.prefab.core.execute_bash(cmd, profile=True)
        self.doneSet('build')

    def _group_exists(self, groupname):
        return groupname in open("/etc/group").read()

    def install(self, reset=False, start=False, port=5432, beta=False):
        if reset is False and self.isInstalled():
            return
        if not self.doneGet('build'):
            self.build(beta=beta)
        cmd = """
        cd {build_dir}
        make install with-pgport={port}
        """.format(build_dir=self.BUILD_DIR, port=port)
        self.prefab.core.dir_ensure(self.dbdir)
        self.prefab.core.execute_bash(cmd, profile=True)
        if not self._group_exists("postgres"):
            self.prefab.core.run('adduser --system --quiet --home $LIBDIR/postgres --no-create-home \
        --shell /bin/bash --group --gecos "PostgreSQL administrator" postgres')
        c = """
        cd $JSAPPSDIR/pgsql
        mkdir data
        mkdir log
        chown -R postgres $JSAPPSDIR/pgsql/
        chown -R postgres {postgresdbdir}
        sudo -u postgres $BINDIR/initdb -D {postgresdbdir} --no-locale
        echo "\nlocal   all             postgres                                md5\n" >> {postgresdbdir}/pg_hba.conf
        """.format(postgresdbdir=self.dbdir)

        # NOTE pg_hba.conf uses the default trust configurations.
        self.prefab.core.execute_bash(c, profile=True)
        if start:
            self.start()

    def configure(self,passwd,dbdir=None):
        """
        #TODO
        if dbdir none then $vardir/postgresqldb/
        """
        if dbdir is not None:
            self.dbdir = dbdir
        self.passwd = passwd


    def start(self):
        """
        Starts postgresql database server and changes the postgres user's password to password set in configure method or using the default `postgres` password
        """
        cmd = """
        chown postgres $JSAPPSDIR/pgsql/log/
        """

        self.prefab.core.execute_bash(cmd, profile=True)

        cmdpostgres = "sudo -u postgres $BINDIR/postgres -D {postgresdbdir}".format(postgresdbdir=self.dbdir)
        self.prefab.processmanager.ensure(name="postgres", cmd=cmdpostgres, env={}, path="", autostart=True)

        # change password
        cmd = """
        sudo -u postgres $BINDIR/psql -c "ALTER USER postgres WITH PASSWORD '{passwd}'"; 
        """.format(passwd=self.passwd)
        self.prefab.core.execute_bash(cmd, profile=True)
        print("user: {}, password: {}".format("postgres", self.passwd))



    def stop(self):
        self.prefab.process.kill("postgres")
