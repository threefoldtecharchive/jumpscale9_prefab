from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabCrm(app):
    NAME = "crm"

    def _init(self):
        self.git_url = "https://github.com/incubaid/crm"
        self.crm_dir = self.replace("$CODEDIR/github/incubaid/crm")

    def build(self):
        """
        Clone the crm repo and install postgresql, caddy, python requirements
        """
        if self.doneGet('build') or self.isInstalled():
            return

        # Install Postgres and python psycopg2 connector
        self.prefab.apps.postgresql.install(start=True)
        self.prefab.development.pip.install("psycopg2")

        # Clone the repository and install python requirements
        self.prefab.development.git.pullRepo(self.git_url, dest=self.crm_dir)
        self.prefab.package.multiInstall(["python3-dev", "libffi-dev"])
        requirements = j.sal.fs.readFile("{}/flaskcrm/requirements.txt".format(self.crm_dir))
        self.prefab.development.pip.multiInstall(requirements)

        # Install Caddy
        self.prefab.apps.caddy.install(plugins=[])

        self.doneSet('build')

    def install(self, reset=False, start=False, host="localhost", db_name="crm", demo=False):
        if reset is False and self.isInstalled():
            return
        if not self.doneGet('build'):
            self.build()

        if not self.doneGet('configure'):
            self.configure(host=host, db_name=db_name, demo=demo)

        if start:
            self.start()

    def configure(self, host, db_name, demo):
        """
        Configure
        """

        # Configure Caddy
        caddy_cfg = """
        #tcpport:80
        {{HOST}}:80
        gzip
        log {{LOGDIR}}/access.log
        proxy / localhost:5000
        errors {
            * {{LOGDIR}}/errors.log
        }
        """
        cfg_params = {
            'HOST': host,
            'LOGDIR': self.replace("{{LOGDIR}}/caddy/log")
        }
        self.prefab.core.dir_ensure(cfg_params["LOGDIR"])
        caddy_cfg = self.replace(caddy_cfg, cfg_params)
        self.prefab.core.file_write(self.replace("$CFGDIR/caddy.cfg"), caddy_cfg)

        # Configure crm app
        crm_cfg = """
BACKEND="postgres"
SQLALCHEMY_DATABASE_URI="postgresql://postgres:postgres@localhost:5432/{db_name}"
        """.format(db_name=db_name)
        self.prefab.core.file_write("{}/flaskcrm/extra.cfg".format(self.crm_dir), crm_cfg)

        # Configure Database
        if not self.prefab.apps.postgresql.isStarted():
            self.prefab.apps.postgresql.start()
        cmd = """
        cd {src_dir}/flaskcrm
        export EXTRA_CONFIG='extra.cfg'
        python3 manage.py resetdb
        """
        if demo:
            cmd += "python3 manage.py loadfixtures"
        cmd = cmd.format(src_dir=self.crm_dir)
        self.prefab.core.run(cmd, profile=True)

        self.doneSet('configure')

    def start(self):
        """
        Start postgres, caddy, crm
        """
        if not self.prefab.apps.postgresql.isStarted():
            self.prefab.apps.postgresql.start()

        if not self.prefab.apps.caddy.isStarted():
            self.prefab.apps.caddy.start()

        cmd = """
        cd {src_dir}/flaskcrm
        export EXTRA_CONFIG='extra.cfg'
        python3 manage.py startapp 
        """.format(src_dir=self.crm_dir)
        self.prefab.core.execute_script(cmd, profile=True)

