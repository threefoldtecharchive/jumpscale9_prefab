from JumpScale import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineAysBot(app):
    NAME = ''

    def isInstalled(self):
        return self.cuisine.core.file_exists(
            "$JSAPPSDIR/ays_bot/telegram-bot") and self.cuisine.core.dir_exists('$JSCFGDIR/ays_bot')

    def __init__(self, executor, cuisine):
        self.cuisine = cuisine
        self.executor = executor
        self._configured = False
        self._instance = ""

    def install(self, start=True, link=True, reset=False):
        """
        python dependencies are:
        Install aysbot
                flask
                python-telegram-bot
        If start is True,
        please configure first
        """
        if not reset and self.isInstalled():
            return

        self.cuisine.bash.fixlocale()

        self.cuisine.development.git.pullRepo('https://github.com/Jumpscale/jscockpit.git')
        if link:
            self.link_code()
        else:
            self.copy_code()

        if start:
            self.start()

    def start(self, token=None, host="0.0.0.0", port=6366, itsyouonlinehost="https://itsyou.online",
              dns=None, client_id=None, client_secret=None, cfg=None, instance='main'):
        """
        token: telegram bot token received from @botfather
        oauth: dict containing
               host
               oauth
               client_id
               client_secret
               itsyouonline.host
        cfg: full dict with config optional
        """
        if not self._configured:
            self.create_config(token, host, port, itsyouonlinehost, dns, client_id, client_secret, cfg, instance)
        cmd = self.replace(
            'jspython ays-bot.py --config $JSCFGDIR/ays_bot/%s/config.toml' % self._instance)
        cwd = self.replace('$JSAPPSDIR/ays_bot')
        self.cuisine.processmanager.ensure('aysbot__%s' % self._instance, cmd=cmd, path=cwd)

    def install_deps(self):
        deps = """
        flask
        python-telegram-bot
        """
        self.cuisine.development.pip.multiInstall(deps, upgrade=True)

    def link_code(self):
        self.cuisine.core.dir_ensure("$JSAPPSDIR")
        self.cuisine.core.file_link('$CODEDIR/github/jumpscale/jscockpit/ays_bot/', '$JSAPPSDIR/ays_bot')

    def copy_code(self):
        self.cuisine.core.dir_ensure("$JSAPPSDIR")
        self.cuisine.core.file_copy('$CODEDIR/github/jumpscale/jscockpit/ays_bot/', '$JSAPPSDIR/', recursive=True)

    def create_config(self, token=None, host="0.0.0.0", port=6366, itsyouonlinehost="https://itsyou.online",
                      dns=None, client_id=None, client_secret=None, cfg=None, instance='main'):
        """
        token: telegram bot token received from @botfather
        dns: str dns key path
        oauth: dict containing
               host
               oauth
               client_id
               client_secret
               itsyouonline.host
        cfg: dict with config optional
        instanc: str name of the instance
        """
        self._configured = True
        if not cfg:
            redirect = "http://%s/callback" % dns
            if not dns:
                redirect = "http://%s:%s/callback" % (host, port)

            cfg = {'token': token,
                   'oauth': {
                       'host': host,
                       'port': port,
                       'organization': client_id,
                       'client_id': client_id,
                       'client_secret': client_secret,
                       'redirect_uri': redirect,
                       'itsyouonlinehost': itsyouonlinehost
                   }
                   }

        config = j.data.serializer.toml.dumps(cfg)
        self.cuisine.core.dir_ensure("$JSCFGDIR/ays_bot")
        self.cuisine.core.file_write("$JSCFGDIR/ays_bot/%s/config.toml" % instance, config)
        self._instance = instance
