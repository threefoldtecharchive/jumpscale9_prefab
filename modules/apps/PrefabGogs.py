from js9 import j
import os
import textwrap

app = j.tools.prefab._getBaseAppClass()

# TODO: *1 needs to be tested prob


class PrefabGogs(app):
    NAME = "gogs"

    def _init(self):
        self._gogspath = str()
        self._gopath = str()
        self._appini = str()
        self.BUILDDIR = self.replace("$BUILDDIR/caddy")
        self.GOGSPATH = self.replace("$GOPATH/src/github.com/gogits/gogs")
        self.CODEDIR = self.GOGSPATH
        self.INIPATH = self.replace("$GOGSPATH/custom/conf/app.ini")

    @property
    def GOPATH(self):
        return self.prefab.runtimes.golang.GOPATH


    def build(self, reset=False):

        if self.doneCheck("build", reset):
            return

        self.prefab.runtimes.golang.install()
        self.prefab.runtimes.golang.glide()

        self.GOGSPATH = self.replace("{}/src/github.com/gogits/gogs".format(self.GOPATH))
        self.CODEDIR = self.GOGSPATH
        self.INIPATH = self.replace("$GOGSPATH/custom/conf/app.ini")

        self.prefab.bash.envSet(
            'GOGITSDIR', '%s/src/github.com/gogits' % self.GOGSPATH)
        self.prefab.bash.envSet('GOGSDIR', '$GOGITSDIR/gogs')

        self.prefab.runtimes.golang.get('golang.org/x/oauth2')
        self.prefab.runtimes.golang.get('github.com/gogits/gogs')

        self.prefab.core.run('cd %s && git remote add gigforks https://github.com/gigforks/gogs' % self.GOGSPATH,
                             profile=True)
        self.prefab.core.run('cd %s && git fetch gigforks && git checkout gigforks/itsyouimpl' % self.GOGSPATH,
                             profile=True, timeout=1200)
        self.prefab.core.run('cd %s && glide install && go build -tags "sqlite cert"' % self.GOGSPATH, profile=True,
                             timeout=1200)

        self.doneSet('build')

    def install(self, reset=False):
        """
        GOGS has no files to move this method is for standardization of prefab
        """
        # TODO: *1 this cannot be right, files should be moved
        return self.build(reset=reset)

    def write_itsyouonlineconfig(self):
        # ADD EXTRA CUSTOM INFO FOR ITS YOU ONLINE.
        if self.doneGet('config'):
            return
        itsyouonlinesection = """\
        [itsyouonline]
        CLIENT_ID     = itsyouref
        CLIENT_SECRET = khZNlrGFiVqHb9u7h6Kh5IvZXY_aE1gWYL_v2Ike9WOZkza4j2k9
        REDIRECT_URL  = http://localhost:3000/oauth/redirect
        AUTH_URL      = https://itsyou.online/v1/oauth/authorize
        TOKEN_URL     = https://itsyou.online/v1/oauth/access_token
        SCOPE        = user:email

        """

        itsyouonlinesection = textwrap.dedent(itsyouonlinesection)
        if self.prefab.core.file_exists(self.INIPATH):
            self.prefab.core.file_write(location=self.INIPATH,
                                        content=itsyouonlinesection,
                                        append=True)
        self.doneSet('config')

    def start(self, name='main'):
        cmd = "{gogspath}/gogs web".format(gogspath=self.GOGSPATH)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='gogs_%s' % name, cmd=cmd)

    def stop(self, name='main'):
        pm = self.prefab.system.processmanager.get()
        pm.stop('gogs_%s' % name)

    def restart(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("gogs")
        self.start()

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        super().reset()
        self.core.dir_remove(self.BUILDDIR)
        self.core.dir_remove(self.CODEDIR)
        self._init()
