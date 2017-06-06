from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabPostgresql(app):
    NAME = "psql"

    def _init(self):
        self.BUILD_DIR = '$TMPDIR/postgresql'

    def build(self):
        if self.doneGet('build') or self.isInstalled():
            return
        postgres_url = 'https://ftp.postgresql.org/pub/source/v9.6.1/postgresql-9.6.1.tar.gz'
        self.prefab.core.file_download(postgres_url, overwrite=False, to=self.BUILD_DIR, expand=True, removeTopDir=True)
        self.prefab.core.dir_ensure("$JSAPPSDIR/pgsql")
        self.prefab.core.dir_ensure("$BINDIR")
        self.prefab.core.dir_ensure("$LIBDIR/postgres")
        self.prefab.package.multiInstall(['build-essential', 'zlib1g-dev', 'libreadline-dev'])
        cmd = """
        cd {}
        ./configure --prefix=$JSAPPSDIR/pgsql --bindir=$BINDIR --sysconfdir=$CFGDIR --libdir=$LIBDIR/postgres --datarootdir=$JSAPPSDIR/pgsql/share
        make
        """.format(self.BUILD_DIR)
        self.prefab.core.execute_bash(cmd, profile=True)
        self.doneSet('build')

    def _group_exists(self, groupname):
        return groupname in open("/etc/group").read()

    def install(self, reset=False, start=False, port=5432):
        if reset is False and self.isInstalled():
            return
        if not self.doneGet('build'):
            self.build()
        cmd = """
        cd {build_dir}
        make install with-pgport={port}
        """.format(build_dir=self.BUILD_DIR, port=port)

        self.prefab.core.execute_bash(cmd, profile=True)
        if not self._group_exists("postgres"):
            self.prefab.core.run('adduser --system --quiet --home $LIBDIR/postgres --no-create-home \
        --shell /bin/bash --group --gecos "PostgreSQL administrator" postgres')
        c = """
        cd $JSAPPSDIR/pgsql
        mkdir data
        mkdir log
        chown  -R postgres $JSAPPSDIR/pgsql/
        sudo -u postgres $BINDIR/initdb -D $JSAPPSDIR/pgsql/data --no-locale
        """
        self.prefab.core.execute_bash(c, profile=True)
        if start:
            self.start()

    def start(self):
        cmd = """
        chown postgres $JSAPPSDIR/pgsql/log/
        sudo -u postgres $BINDIR/pg_ctl -D $JSAPPSDIR/pgsql/data -l $JSAPPSDIR/pgsql/log/logfile start
        """
        self.prefab.core.execute_bash(cmd, profile=True)

    def stop(self):
        cmd = """
        sudo -u postgres $BINDIR/pg_ctl -D $JSAPPSDIR/pgsql/data -l $JSAPPSDIR/pgsql/log/logfile stop
        """
        self.prefab.core.execute_bash(cmd, profile=True)
