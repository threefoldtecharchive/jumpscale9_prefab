from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabMattermostBot(app):
    NAME = "matterbot"

    def _init(self):
        self.bot_repo = "https://github.com/gigforks/mattermost_bot.git"
        self.bot_path = "{{CODEDIR}}/mattermost_bot"

    def build(self, reset=False):
        if self.doneCheck('build', reset):
            return

        # Clone bot server repo
        self.prefab.tools.git.pullRepo(self.bot_repo, dest=self.bot_path)
        self.doneSet('build')

    def install(self, api_url, bot_user, bot_email, bot_password, reset=False):
        """
        Build and Install mattermost bot
        :param api_url: mattermost chat api url (e.g. https://chat.grid.tf)
        :param bot_user: the name which will be used by the bot
        :param bot_email: the email which will be used for the bot user
        :param bot_password: bot user password
        :param start: start after install
        :param reset: reset building
        """
        if self.doneCheck("install", reset):
            return
        self.build(reset=reset)
        self._configure("{}/api/v4".format(api_url), bot_user, bot_email, bot_password, reset=reset)
        cmd = "cd {bot_path} && python3 setup.py install".format(bot_path=self.bot_path)
        self.prefab.core.run(cmd)
        self.doneSet('install')

    def _configure(self, api_url, bot_user, bot_email, bot_password, reset=False):
        if self.doneCheck("configure", reset):
            return
        cmd = """
        cd /opt/mattermost/
        ./bin/platform user create --email='{bot_email}' --password='{bot_password}' --username='{bot_user}'
        ./bin/platform user verify {bot_user}
        """.format(bot_user=bot_user, bot_password=bot_password, bot_email=bot_email)
        self.prefab.core.run(cmd)
        config_file_path = "{}/local_settings.py".format(self.bot_path)
        config_data = {
            "BOT_URL": api_url,
            "BOT_LOGIN": bot_email,
            "BOT_PASSWORD": bot_password,
        }
        config_data = j.data.serializer.toml.dumps(config_data)
        self.prefab.core.file_write(config_file_path, config_data)
        self.doneSet('configure')

    def start(self):
        self.prefab.system.processmanager.get().ensure("mattermost-bot", "matterbot", path=self.bot_path,
                                                       env={"MATTERMOST_BOT_SETTINGS_MODULE": "local_settings"})

    def stop(self):
        self.prefab.system.processmanager.get().stop("mattermost-bot")
