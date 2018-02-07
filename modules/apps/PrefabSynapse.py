from js9 import j
import textwrap

app = j.tools.prefab._getBaseAppClass()


class PrefabSynapse(app):
    NAME = "synapse"


    def build(self, reset=False):
        """
        build from pythong
        """

        if self.doneCheck('build', reset):
            return

        self._installDeps()

        #PUT THE BUILD CODE HERE

        self._configure()

        self.doneSet('build')

    def _installDeps(self):
        """

        database on postgresql

        """

        self.prefab.system.package.mdupdate()
        self.prefab.runtimes.python.install()
        self.prefab.db.postgresql.install()


    def _configure(self):
        """Configure synapse
        Configure: db
        """

        # Configure Database
        config = """
        """
        self.prefab.core.file_write(location=self.INIPATH,content=config)

    def install(self, adminpasswd, reset=False, start=False):
        """


        Keyword Arguments:
            reset {bool} -- force build if True (default: {False})
        """

        self.build(reset=reset)

        # # Create postgres db
        self.prefab.core.run('sudo -u postgres /opt/bin/psql -c \'create database synapse;\'', die=False)
        self.start()
        cmd = """
        sudo -u postgres /opt/bin/psql synapse -c
        "INSERT INTO login_source (type, name, is_actived, cfg, created_unix, updated_unix)
        VALUES (6, 'Itsyou.online', TRUE,
        '{\\"Provider\\":\\"itsyou.online\\",\\"ClientID\\":\\"%s\\",\\"ClientSecret\\":\\"%s\\",\\"OpenIDConnectAutoDiscoveryURL\\":\\"\\",\\"CustomURLMapping\\":null}',
        extract('epoch' from CURRENT_TIMESTAMP) , extract('epoch' from CURRENT_TIMESTAMP));"
        """
        cmd = cmd % (org_client_id, org_client_secret)
        cmd = cmd.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        self.prefab.core.run(cmd)
        if not start:
            self.stop()
            self.prefab.db.postgresql.stop()

    def start(self, name='main'):
        """Start synapse server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()
        cmd = '{synapsepath}/synapse web'.format(synapsepath=self.synapsePATH)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='synapse_%s' % name, cmd=cmd)

    def stop(self, name='main'):
        """Stop synapse server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """

        pm = self.prefab.system.processmanager.get()
        pm.stop('synapse_%s' % name)

    def restart(self, name='main'):
        """Stop synapse server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop('synapse_%s' % name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        super().reset()
        self.core.dir_remove(self.CODEDIR)
        self._init()
