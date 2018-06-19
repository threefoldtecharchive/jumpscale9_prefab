from js9 import j
import textwrap

app = j.tools.prefab._getBaseAppClass()

class PrefabMattermost(app):
    NAME = "mattermost"

    @property
    def GOPATH(self):
        return self.prefab.runtimes.golang.GOPATH

    def build(self, dbpass, reset=False):
        if self.doneCheck('build', reset):
            return

        self._installDeps()
        self.prefab.db.mariadb.start()
        self.prefab.db.mariadb._create_db("mattermost")
        self.prefab.db.mariadb.admin_create('mmuser', dbpass)
        self.prefab.runtimes.golang.get("github.com/mattermost/mattermost-server/cmd/...", install=False)
        self.prefab.tools.git.pullRepo("https://github.com/gigforks/mattermost-webapp.git", branch="master", dest="%s/src/github.com/mattermost/mattermost-webapp" % self.GOPATH)
        root_path = "%s/src/github.com/mattermost" % self.GOPATH
        self.prefab.core.run('cd %s/mattermost-server && git remote add gigforks https://github.com/gigforks/mattermost-server' % root_path,
                             profile=True)
        self.prefab.core.run('cd %s/mattermost-server && git fetch gigforks && git checkout gigforks/master' % root_path,
                             profile=True, timeout=1200)
        self.prefab.core.run('cp {rootpath}/mattermost-server/config/default.json {rootpath}/mattermost-server/config/config.json'.format(rootpath=root_path))
        self.prefab.core.run("sed -i 's/dockerhost/localhost/g' %s/mattermost-server/config/config.json" % root_path)
        self.prefab.core.run("sed -i 's/mostest/%s/g' %s/mattermost-server/config/config.json" % (dbpass, root_path))
        self.prefab.core.run("sed -i 's/mattermost_test/mattermost/g' %s/mattermost-server/config/config.json" % (root_path))
        self.prefab.core.run("cd %s/mattermost-webapp && make package" % root_path, timeout=2000)
        self.prefab.core.run("cd %s/mattermost-server && make build && make package" % root_path)

        self.doneSet('build')

    def _installDeps(self):
        """Install mattermost deps

        sys packages: git-core, gcc, golang
        db: mariadb
        """

        self.prefab.system.package.mdupdate()
        self.prefab.system.package.ensure('git-core')
        self.prefab.system.package.ensure('postfix')
        self.prefab.system.package.ensure('gcc')
        self.prefab.system.package.ensure('make')
        self.prefab.runtimes.golang.install()
        self.prefab.core.run('curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -')
        self.prefab.system.package.ensure('nodejs')
        self.prefab.system.package.ensure('pngquant')
        self.prefab.system.package.ensure('zip')
        self.prefab.db.mariadb.install()

    def install(self, dbpass, reset=False, start=True):
        """Build Mattermost with itsyou.online config

        Same as build but exists for standarization sake

        Keyword Arguments:
            reset {bool} -- force build if True (default: {False})
        """
        if self.doneCheck('install', reset):
            return

        self.build(dbpass)
        self.prefab.core.run('cp -r %s/src/github.com/mattermost/mattermost-server/dist/mattermost /opt/' % self.GOPATH)
        self.prefab.core.run('cp %s/bin/platform /opt/mattermost/bin' % self.GOPATH)
        self.prefab.core.dir_ensure('/opt/mattermost/client')
        self.prefab.core.run('cp -r %s/src/github.com/mattermost/mattermost-webapp/dist/* /opt/mattermost/client' % self.GOPATH)
        self.prefab.core.dir_ensure('/opt/mattermost/bin/plugins')
        self.prefab.core.dir_ensure('/opt/mattermost/bin/data')

        self.doneSet('install')
        if start:
            self.start()

    def start(self, name='main'):
        """Start Mattermost server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """
        cmd = 'cd /opt/mattermost && ./bin/platform'
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='mattermost_%s' % name, cmd=cmd)

    def stop(self, name='main'):
        """Stop Mattermost server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """

        pm = self.prefab.system.processmanager.get()
        pm.stop('mattermost_%s' % name)

    def restart(self, name='main'):
        """Restarts Mattermost server instance

        Keyword Arguments:
            name {string} -- name of the server instance (default: {'main'})
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop('mattermost_%s' % name)
        self.start(name)

