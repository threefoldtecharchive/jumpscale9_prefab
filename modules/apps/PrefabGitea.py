from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabGitea(app):
    NAME = "gitea"

    def _init(self):
        self._gogspath = str()
        self._gopath = str()
        self._appini = str()
        self.BUILDDIR = self.replace('$BUILDDIR/caddy')
        self.GITEAPATH = self.replace('$GOPATH/src/code.gitea.io/gitea')
        self.CODEDIR = self.GITEAPATH
        self.INIPATH = self.replace('$GITEAPATH/custom/conf/app.ini')

    @property
    def GOPATH(self):
        return self.prefab.runtimes.golang.GOPATH

    def build(self, reset=False):
        """Build Gitea with itsyou.online config

        Keyword Arguments:
            reset {bool} -- force build if True (default: {False})
        """

        if self.doneCheck('build', reset):
            return

        # install dependencies
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.ensure('git-core')
        self.prefab.system.package.ensure('gcc')
        self.prefab.runtimes.golang.install()

        # set needed paths
        self.GITEAPATH = self.replace('{}/src/code.gitea.io/gitea'.format(self.GOPATH))
        self.CUSTOM_PATH = self.replace('$GITEAPATH/custom')
        self.CODEDIR = self.GITEAPATH
        self.INIPATH = self.replace('%s/conf/app.ini' % self.CUSTOM_PATH)

        # set env vars
        self.prefab.bash.envSet(
            'GITEAITSDIR', '%s/src/github.com/gigforks' % self.GITEAPATH)
        self.prefab.bash.envSet('GITEADIR', '$GITEAITSDIR/gitea')

        self.prefab.runtimes.golang.get('code.gitea.io/gitea')

        # change branch from master to gigforks/iyo_integration
        self.prefab.core.run('cd %s && git remote add gigforks https://github.com/gigforks/gitea' % self.GITEAPATH,
                             profile=True)
        self.prefab.core.run('cd %s && git fetch gigforks && git checkout gigforks/iyo_integration' % self.GITEAPATH,
                             profile=True, timeout=1200)

        # gitea-custom is needed to replace the default gitea custom
        self.prefab.tools.git.pullRepo("https://github.com/incubaid/gitea-custom.git", branch="master")
        if not self.prefab.core.file_is_link(self.CUSTOM_PATH):
            self.prefab.core.dir_remove(self.CUSTOM_PATH)

        self.prefab.core.file_link(source='/opt/code/github/incubaid/gitea-custom',
                                   destination=self.CUSTOM_PATH)

        # build gitea (will be stored in self.GITEAPATH/gitea)
        self.prefab.core.run('cd %s && TAGS="bindata" make generate build' % self.GITEAPATH, profile=True,
                             timeout=1200)
        self.doneSet('build')

    def install(self, reset=False):
        """Build Gitea with itsyou.online config

        Same as build but exists for standarization sake

        Keyword Arguments:
            reset {bool} -- force build if True (default: {False})
        """

        self.build(reset=reset)

    def start(self, name='main'):
        """Start GITEA server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """

        cmd = '{giteapath}/gitea web'.format(giteapath=self.GITEAPATH)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='gitea_%s' % name, cmd=cmd)

    def stop(self, name='main'):
        """Stop GITEA server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """

        pm = self.prefab.system.processmanager.get()
        pm.stop('gitea_%s' % name)

    def restart(self, name='main'):
        """Stop GITEA server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop('gitea_%s' % name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        super().reset()
        self.core.dir_remove(self.BUILDDIR)
        self.core.dir_remove(self.CODEDIR)
        self._init()
