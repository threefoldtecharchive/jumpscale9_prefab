from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabSynapse(app):
    NAME = "synapse"

    def _init(self):
        self.server_path = "/root/.synapse"
        self.client_path = "/opt/var/riot"
        self.client_url = "https://github.com/vector-im/riot-web/releases/download/v0.13.5/riot-v0.13.5.tar.gz"

    def build(self, reset=False):
        if self.doneCheck('build', reset):
            return

        # Install prerequisite libraries
        self.prefab.system.package.mdupdate()
        needed_packages = [
            "build-essential", "python2.7", "python2.7-dev", "libffi-dev",
            "python-pip", "python-virtualenv", "python-setuptools", "libssl-dev",
            "libjpeg-dev", "libxslt1-dev", "libpq-dev"
        ]
        for package in needed_packages:
            self.prefab.system.package.ensure(package)

        # Install Postgresql and caddy
        if not self.prefab.db.postgresql.isInstalled():
            self.prefab.db.postgresql.install()
        if not self.prefab.web.caddy.isInstalled():
            self.prefab.web.caddy.install(plugins=["iyo"])

        # Install prerequisite python libs
        cmd = """
        virtualenv -p python2.7 {server_path}
        source /root/.synapse/bin/activate
        pip install --upgrade pip
        pip install --upgrade setuptools
        pip install psycopg2-binary 
        """.format(server_path=self.server_path)
        self.prefab.core.run(cmd)

        # Download the riot web client for matrix
        self.prefab.core.file_download(self.client_url, to=self.client_path, expand=True, removeTopDir=True)

        self.doneSet('build')

    def install(self, admin_username, admin_password, domain="localhost", client_port=8080,
                reset=False, start=False):
        """
        Build and Install synapse matrix server and web client
        :param admin_username: the username of synapse admin that will be created
        :param admin_password: password of the synapse admin
        :param domain: the domain that will serve the synapse server without https://
        :param client_port: the port on which the web client will be served
        :param reset: if you need to reset the installation
        :param start: if you need to start server after installation
        :return:
        """
        self.build(reset=reset)

        # Install synapse using pip
        cmd = """
        source {}/bin/activate
        pip install https://github.com/matrix-org/synapse/tarball/master
        """.format(self.server_path)
        self.prefab.core.run(cmd)

        # Create database if not exists
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()
        db_query = """
                CREATE DATABASE synapse
                ENCODING 'UTF8'
                LC_COLLATE='C'
                LC_CTYPE='C'
                template=template0
            """
        self.prefab.core.run('sudo -u postgres /opt/bin/psql -c "{}"'.format(db_query), die=False)

        # Configure synapse server and riot client
        self._configure(user=admin_username, password=admin_password,
                        domain=domain, client_port=client_port)
        if not start:
            self.stop()

    def _configure(self, user, password, domain, client_port):

        # Generate config file homeserver.yaml
        cmd = """
        cd {}
        source ./bin/activate
        python -m synapse.app.homeserver \
            --server-name {} \
            --config-path homeserver.yaml \
            --generate-config \
            --report-stats=yes
        """.format(self.server_path, domain)
        self.prefab.core.run(cmd)

        config_file_path = "{}/homeserver.yaml".format(self.server_path)
        config_data = self.prefab.core.file_read(config_file_path)
        config_data = j.data.serializer.yaml.loads(config_data)
        config_data["database"] = {
            "name": "psycopg2",
            "args": {
                "user": "postgres",
                "password": "postgres",
                "database": "synapse",
                "host": "localhost",
                "cp_min": 5,
                "cp_max": 10,
            }
        }
        config_data["enable_registration"] = True
        config_data = j.data.serializer.yaml.dumps(config_data)
        self.prefab.core.file_write(config_file_path, config_data)

        # Edit config file of the riot client to refer to our own matrix
        config_file_path = "{}/config.sample.json".format(self.client_path)
        config_data = self.prefab.core.file_read(config_file_path)
        config_data = j.data.serializer.json.loads(config_data)
        config_data["default_hs_url"] = "https://{}".format(domain)
        config_data = j.data.serializer.yaml.dumps(config_data)
        self.prefab.core.file_write("{}/config.json".format(self.client_path), config_data)

        # Create admin user
        self.start()
        cmd = """
        cd {server_path}
        source ./bin/activate
        register_new_matrix_user -c homeserver.yaml -u {user} -p {password} -a https://localhost:8448
        """.format(server_path=self.server_path, user=user, password=password)
        self.prefab.core.run(cmd)

        # Create Caddy config file to serve the web client
        caddy_cfg = """
        :{{client_port}} {
            bind 0.0.0.0
            gzip
            browse
            root {{client_path}}
        }
        """
        caddy_cfg = self.replace(caddy_cfg, {
            "client_path": self.client_path,
            "client_port": client_port,
        })
        self.prefab.web.caddy.add_website("riot_client", caddy_cfg)

    def start(self):
        self.stop()
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()
        cmd = """
        cd {}
        source ./bin/activate
        synctl start
        """.format(self.server_path)
        self.prefab.core.run(cmd)

    def stop(self):
        cmd = """
        cd {}
        source ./bin/activate
        synctl stop
        """.format(self.server_path)
        self.prefab.core.run(cmd, die=False)
