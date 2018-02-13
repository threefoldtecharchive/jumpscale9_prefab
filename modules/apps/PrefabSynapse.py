from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabSynapse(app):
    NAME = "synapse"

    def build(self, reset=False):
        if self.doneCheck('build', reset):
            return

        self.prefab.system.package.mdupdate()
        needed_packages = [
            "build-essential", "python2.7", "python2.7-dev", "libffi-dev",
            "python-pip", "python-virtualenv", "python-setuptools", "libssl-dev",
            "libjpeg-dev", "libxslt1-dev", "libpq-dev"
        ]
        for package in needed_packages:
            self.prefab.system.package.ensure(package)

        self.prefab.db.postgresql.install()
        self.prefab.web.caddy.install(plugins=["iyo"])
        cmd = """
        virtualenv -p python2.7 /root/.synapse
        source /root/.synapse/bin/activate
        pip install --upgrade pip
        pip install --upgrade setuptools
        pip install psycopg2
        """
        self.prefab.core.run(cmd)
        self.doneSet('build')

    def install(self, admin_username, admin_password, domain="localhost", reset=False, start=False):
        self.build(reset=reset)

        # Install synapse using pip
        cmd = """
        pip install https://github.com/matrix-org/synapse/tarball/master
        """
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
        self._configure(user=admin_username, password=admin_password, domain=domain)
        if not start:
            self.stop()

    def _configure(self, user, password, domain):
        cmd = """
        cd /root/.synapse
        source ./bin/activate
        python -m synapse.app.homeserver \
            --server-name {} \
            --config-path homeserver.yaml \
            --generate-config \
            --report-stats=yes
        """.format(domain)
        self.prefab.core.run(cmd)

        config_file_path = "/root/.synapse/homeserver.yaml"
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

        self.start()
        cmd = """
        cd /root/.synapse
        source ./bin/activate
        register_new_matrix_user -c homeserver.yaml -u {user} -p {password} -a https://localhost:8448
        """.format(user=user, password=password)
        self.prefab.core.run(cmd)

    def start(self):
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()
        cmd = """
        cd /root/.synapse
        source ./bin/activate
        synctl start
        """
        self.prefab.core.run(cmd)

    def stop(self):
        cmd = """
        cd /root/.synapse
        source ./bin/activate
        synctl stop
        """
        self.prefab.core.run(cmd)

    def restart(self):
        self.stop()
        self.start()
