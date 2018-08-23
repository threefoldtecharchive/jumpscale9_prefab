from jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabSynapsebot(app):
    NAME = "synapse-bot"

    def _init(self):
        self.bot_repo = "https://github.com/arahmanhamdy/Matrix-NEB.git"
        self.server_path = "{{CODEDIR}}/matrixbot"

    def build(self, reset=False):
        if self.doneCheck('build', reset):
            return

        # Install prerequisite libraries
        self.prefab.system.package.mdupdate()
        needed_packages = ["python3-pip", "python3-setuptools"]
        for package in needed_packages:
            self.prefab.system.package.ensure(package)

        # Clone bot server repo
        self.prefab.tools.git.pullRepo(self.bot_repo, dest=self.server_path)

        # Install prerequisite python libs
        cmd = """
        cd {server_path}
        python3 setup.py install
        """.format(server_path=self.server_path)
        self.prefab.core.run(cmd)

        self.doneSet('build')

    def install(self, matrix_url, bot_user, admins=None, start=True, reset=False):
        """
        Build and Install synapse matrix bot server
        :param matrix_url: Synapse matrix url
        :param bot_user: the full username of bot user (i.e @gigbot:matrix.aydo.com)
        :param admins:list: list of full username of admins of the bot (i.e ["@root:matrix.aydo.com"])
        :param start: start after install
        :param reset: reset building
        """

        self.build(reset=reset)
        # Configure synapse bot server
        self._configure(matrix_url, bot_user, admins)
        if start:
            self.start()

    def _configure(self, matrix_url, bot_user, admins=None):
        import requests
        if not admins:
            admins = []

        # create bot user
        bot = {"username": bot_user, "password": "", "auth": {"type": "m.login.dummy"}}
        res = requests.post("{}/_matrix/client/r0/register".format(matrix_url), json=bot)
        token = res.json()['access_token']

        # configure bot server to use the bot user
        config_file_path = "{}/botserver.conf".format(self.server_path)
        config_data = {
            "url": matrix_url,
            "case_insensitive": True,
            "token": token,
            "admins": admins,
            "user": bot_user
        }
        config_data = j.data.serializers.json.dumps(config_data)
        self.prefab.core.file_write(config_file_path, config_data)

    def start(self):
        cmd = 'python3 "{}" -c "{}"'.format(self.server_path + "/neb.py", self.server_path + "/botserver.conf")
        self.prefab.system.processmanager.get().ensure("matrix-bot", cmd, wait=5, expect="Running on")

    def stop(self):
        self.prefab.system.processmanager.get().stop("matrix-bot")
