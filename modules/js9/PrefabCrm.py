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

        self.prefab.system.package.mdupdate()

        # Install build-essential
        self.prefab.system.package.install("build-essential")

        # install git
        self.prefab.system.package.install(["git"])

        # Install apt requirements
        requirements = j.sal.fs.readFile("{}/requirements.apt".format(self.crm_dir))
        self.prefab.system.package.install(requirements)

        # Install pip requirements
        requirements = j.sal.fs.readFile("{}/requirements.pip".format(self.crm_dir))
        self.prefab.runtimes.pip.multiInstall(requirements)

        # Clone the repository and install python requirements
        self.prefab.tools.git.pullRepo(self.git_url, dest=self.crm_dir, branch="production")

        # Install Caddy
        self.prefab.web.caddy.build(plugins=['iyo', 'git', 'mailout'], reset=True)
        self.prefab.web.caddy.install(reset=True)

        # Install and start Postgres
        self.prefab.db.postgresql.install()
        self.prefab.db.postgresql.start()

        # Install redis
        self.prefab.db.redis.install()
        self.prefab.db.redis.start()

        self.doneSet('build')

    def install(self, reset=False, start=False, domain="localhost", caddy_port=80, db_name="crm", demo=False,
                client_id=None, client_secret=None, tls="off", sendgrid_api_key=None, support_email=None):
        if reset is False and self.isInstalled():
            return
        if not self.doneGet('build'):
            self.build()

        if not self.doneGet('configure'):
            self.configure(
                domain=domain,
                caddy_port=caddy_port,
                db_name=db_name,
                demo=demo,
                client_id=client_id,
                client_secret=client_secret,
                sendgrid_api_key=sendgrid_api_key,
                support_email=support_email,
                tls=tls)

        if start:
            self.start(sendgrid_api_key=sendgrid_api_key, support_email=support_email)

    def configure(self, domain, caddy_port, db_name, demo, client_id, client_secret, sendgrid_api_key, support_email, tls):
        """
        Configure
        """

        # Configure Caddy
        log_dir = self.replace("{{LOGDIR}}/caddy/log")

        if caddy_port == 443:
            listen = domain
            scheme = "https"
        else:
            listen = "{}:{}".format(domain, caddy_port)
            scheme = "http"

        caddy_cfg = """
        #tcpport:{PORT}
        {LISTEN}
        gzip
        log {LOGDIR}/access.log
        proxy / localhost:5000 {{
            header_upstream Host "{DOMAIN}"
            except /docs/graphqlapi
        }}
        root {CRM_DIR}
        browse docs/graphqlapi/index.html
        errors {{
            * {LOGDIR}/errors.log
        }}
        tls {TLS}
        """.format(LISTEN=listen, PORT=caddy_port, LOGDIR=log_dir, DOMAIN=domain, TLS=tls, CRM_DIR=self.crm_dir)

        if client_id and client_secret:
            caddy_cfg += """
            oauth {{
                client_id                       {CLIENT_ID}
                client_secret                   {CLIENT_SECRET}
                redirect_url                    {SCHEME}://{LISTEN}/iyo_callback
                extra_scopes                    user:address,user:email,user:phone,user:memberof:threefold.crm_users
                allow_extension                 api
                allow_extension                 graphql
                authentication_required         /
                allow_extension html
                allow_extension graphqlapi
                allow_extension png
            }}
            """.format(CLIENT_ID=client_id, CLIENT_SECRET=client_secret, SCHEME=scheme, DOMAIN=domain, LISTEN=listen)
        self.prefab.core.dir_ensure(log_dir)
        self.prefab.core.file_write(self.replace("$CFGDIR/caddy.cfg"), caddy_cfg)

        # Configure Database
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()

        cmd = """
        cd {src_dir}
        export SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/{db_name}
        export CACHE_BACKEND_URI=redis://127.0.0.1:6379/0
        export SENDGRID_API_KEY={sendgrid_api_key}
        export SUPPORT_EMAIL={support_email}
        export ENV=prod
        export FLASK_APP=app.py
        flask createdb
        flask db upgrade
        """
        if demo:
            cmd += "flask loadfixtures"
        cmd = cmd.format(src_dir=self.crm_dir, db_name=db_name, sendgrid_api_key=sendgrid_api_key, support_email=support_email)
        self.prefab.core.run(cmd, profile=True)

        self.doneSet('configure')

    def start(self, db_name="crm", sendgrid_api_key=None, support_email=""):
        """
        Start postgres, caddy, crm
        """
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()

        if not self.prefab.db.redis.isStarted():
            self.prefab.db.redis.start()

        if not self.prefab.web.caddy.isStarted():
            self.prefab.web.caddy.start()

        cmd = "cd {src_dir};"
        cmd += "export SQLALCHEMY_DATABASE_URI=postgresql://postgres:postgres@localhost:5432/{db_name};"
        cmd += "export CACHE_BACKEND_URI=redis://127.0.0.1:6379/0;"
        cmd += "export SENDGRID_API_KEY={sendgrid_api_key};"
        cmd += "export SUPPORT_EMAIL={support_email};"
        cmd += "export ENV=prod;export FLASK_APP=app.py;"
        cmd = cmd.format(src_dir=self.crm_dir, db_name=db_name, support_email=support_email,
                             sendgrid_api_key=sendgrid_api_key)
        crm_cmd = cmd + "flask db upgrade; uwsgi --ini uwsgi.ini"
        mailer_cmd = cmd + "flask mailer"
        sync_data_cmd = cmd  + "flask syncdata"
        rq_worker_cmd = cmd + "flask rq_worker"

        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="crm", cmd=crm_cmd, autostart=True)
        pm.ensure(name="mailer", cmd=mailer_cmd, autostart=True)
        pm.ensure(name="syncdata", cmd=sync_data_cmd, autostart=True)
        pm.ensure(name="rq_worker", cmd=rq_worker_cmd, autostart=True)
