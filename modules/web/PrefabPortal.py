from js9 import j
import time
import os


base = j.tools.prefab._getBaseClass()


class PrefabPortal(base):

    def _init(self):
        self.portal_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths["JSAPPSDIR"], "portals/")
        self.main_portal_dir = j.sal.fs.joinPaths(self.portal_dir, 'main')

    def configure(
            self,
            mongodbip="127.0.0.1",
            mongoport=27017,
            production=True,
            client_id='',
            client_secret='',
            organization='',
            redirect_address=''):

        # go from template dir which go the file above
        content = self.prefab.core.file_read('$TEMPLATEDIR/cfg/portal/config.yaml')

        cfg = j.data.serializer.yaml.loads(content)
        cfg['production'] = production

        if production:
            cfg['oauth.client_id'] = client_id
            cfg['oauth.client_scope'] = 'user:email:main,user:memberof:%s' % client_id
            cfg['oauth.client_secret'] = client_secret
            cfg['force_oauth_instance'] = 'itsyou.online'
            cfg['oauth.default_groups'] = ['admin', 'user']
            cfg['oauth.organization'] = organization
            cfg['oauth.redirect_url'] = 'http://%s/restmachine/system/oauth/authorize' % redirect_address
        # ITS ALREADY THE DEFAULT IN THE CONFIG DIR
        # cfg['param.cfg.appdir'] = j.sal.fs.joinPaths(self.portal_dir, 'portalbase')

        cfg['mongoengine.connection'] = {'host': mongodbip, 'port': mongoport}
        self.prefab.core.file_write(self.configPath, j.data.serializer.yaml.dumps(cfg))

    @property
    def configPath(self):
        return j.sal.fs.joinPaths(self.prefab.core.dir_paths['CFGDIR'],
                                  "portals", "main", "config.yaml")

    def install(self, start=True, branch='master', reset=False):
        """
        grafanaip and port should be the external ip of the machine
        Portal install will only install the portal and libs. No spaces but the system ones will be add by default.
        To add spaces and actors, please use addSpace and addactor
        """
        self.logger.info("Install prefab portal on branch:'%s'" % branch)
        self.prefab.core.dir_ensure(self.main_portal_dir)
        self.prefab.bash.fixlocale()
        if not reset and self.doneGet("install"):
            self.linkCode()
            if start:
                self.start()
            return

        self.prefab.db.mongodb.install()
        self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("$BINDIR"))
        self.prefab.bash.profileDefault.save()

        # install the dependencies if required
        self.getcode(branch=branch)
        self.installDeps(reset=reset)

        # pull repo with required branch ; then link dirs and files in required places
        self.linkCode()

        if start:
            self.start()

        self.doneSet("install")

    def installNodeJSLibs(self):
        self.prefab.apps.nodejs.install()  # will install nodejs & bower, used to build the libs if we need it
        self.prefab.apps.nodejs.bowerInstall(["jquery",
                                               "flatui",
                                               "bootstrap",
                                               "famous",
                                               "codemirror",
                                               "font-awesome",
                                               "jqplot",
                                               "underscore",
                                               "spin",
                                               "moment",
                                               "http://DlhSoft.com/Packages/DlhSoft.KanbanLibrary.zip",
                                               "jqwidgets",
                                               "d3"])  # , "angular-latest"])

    def installDeps(self, reset=False):
        """
        make sure new env arguments are understood on platform
        """
        if not reset and self.doneGet("installdeps"):
            return

        if "darwin" not in self.prefab.platformtype.osname:
            self.prefab.system.package.ensure('build-essential')
            self.prefab.system.package.ensure('libssl-dev')
            self.prefab.system.package.ensure('libffi-dev')
            self.prefab.system.package.ensure('python3-dev')

        if "darwin" in self.prefab.platformtype.osname:
            self.prefab.system.package.multiInstall(['libtiff', 'libjpeg', 'webp', 'little-cms2', 'snappy'])
            self.prefab.core.run('CPPFLAGS="-I/usr/local/include -L/usr/local/lib" pip3 install python-snappy')
        else:
            self.prefab.system.package.multiInstall(['libjpeg-dev', 'libffi-dev', 'zlib1g-dev'])

        # snappy install
        if "darwin" not in self.prefab.platformtype.osname:
            self.prefab.system.package.ensure('libsnappy-dev')
            self.prefab.system.package.ensure('libsnappy1v5')
            self.prefab.development.pip.install('python-snappy')

        cmd = """
            cd {CODEDIR}/github/jumpscale/portal9
            pip3 install -e .
            """.format(CODEDIR=self.prefab.core.dir_paths["CODEDIR"])
        self.prefab.core.execute_bash(cmd)
        self.doneSet("installdeps")

    def getcode(self, branch='master'):
        self.logger.info("Get portal code on branch:'%s'" % branch)
        if branch == "":
            branch = os.environ.get('JSBRANCH')
        self.prefab.tools.git.pullRepo(
            "https://github.com/Jumpscale/portal9.git", branch=branch)

    def linkCode(self):

        if not self.portal_dir.endswith("/"):
            self.portal_dir += '/'
        self.prefab.core.dir_ensure(self.portal_dir)

        CODE_DIR = self.prefab.core.dir_paths["CODEDIR"]
        self.prefab.core.file_link("%s/github/jumpscale/portal9/jslib" % CODE_DIR,
                                    '%s/jslib' % self.portal_dir)
        self.prefab.core.dir_ensure(j.sal.fs.joinPaths(self.portal_dir, 'portalbase'))
        self.prefab.core.file_link("%s/github/jumpscale/portal9/apps/portalbase/system" % CODE_DIR,
                                    '%s/portalbase/system' % self.portal_dir)
        self.prefab.core.file_link("%s/github/jumpscale/portal9/apps/portalbase/wiki" % CODE_DIR,
                                    '%s/portalbase/wiki' % self.portal_dir)
        self.prefab.core.file_link("%s/github/jumpscale/portal9/apps/portalbase/macros" %
                                    CODE_DIR, '%s/portalbase/macros' % self.portal_dir)
        self.prefab.core.file_link("%s/github/jumpscale/portal9/apps/portalbase/templates" %
                                    CODE_DIR, '%s/portalbase/templates' % self.portal_dir)

        self.prefab.core.dir_ensure(self.main_portal_dir)

        self.prefab.core.dir_ensure('%s/base/' % self.main_portal_dir)

        self.prefab.core.dir_ensure('$TEMPLATEDIR/cfg/portal')
        self.prefab.core.file_copy(
            j.sal.fs.joinPaths(
                CODE_DIR,
                'github/jumpscale/portal9/apps/portalbase/config.yaml'),
            '$TEMPLATEDIR/cfg/portal/config.yaml')
        self.prefab.core.dir_ensure("$CFGDIR/portals/main/")
        self.prefab.core.file_copy(
            j.sal.fs.joinPaths(
                CODE_DIR,
                'github/jumpscale/portal9/apps/portalbase/config.yaml'),
            "$CFGDIR/portals/main/config.yaml")
        # copy portal_start.py
        self.prefab.core.file_copy(
            j.sal.fs.joinPaths(
                CODE_DIR,
                'github/jumpscale/portal9/apps/portalbase/portal_start.py'),
            self.main_portal_dir)
        self.prefab.core.file_copy("%s/jslib/old/images" % self.portal_dir,
                                    "%s/jslib/old/elfinder" % self.portal_dir, recursive=True)
        # link spaces
        spaces = j.tools.prefab.local.core.find(
            '$CODEDIR/github/jumpscale/portal9/apps/portalbase/',
            recursive=True,
            pattern='*.space',
            type='d')
        to_link = [j.sal.fs.getParent(x) for x in spaces]
        for space in to_link:
            space_name = j.sal.fs.getBaseName(space)
            if space_name not in ['home', 'TestWebsite', 'TestSpace']:
                self.prefab.core.file_link(source=space, destination='$JSAPPSDIR/portals/main/base/%s' % space_name)

    def addSpace(self, spacepath):
        spacename = j.sal.fs.getBaseName(spacepath)
        dest_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths[
            'JSAPPSDIR'], 'portals', 'main', 'base', spacename)
        self.prefab.core.file_link(spacepath, dest_dir)

    def addActor(self, actorpath):
        actorname = j.sal.fs.getBaseName(actorpath)
        dest_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths[
            'JSAPPSDIR'], 'portals', 'main', 'base', actorname)
        self.prefab.core.file_link(actorpath, dest_dir)

    def start(self, passwd=None):
        """
        Start the portal
        passwd : if not None, change the admin password to passwd after start
        """
        self.prefab.db.mongodb.start()
        cmd = "python3 portal_start.py"
        pm = self.prefab.system.processManager.get()
        pm.ensure('portal', cmd=cmd, path=j.sal.fs.joinPaths(self.portal_dir, 'main'))

        if passwd is not None:
            self.set_admin_password(passwd)

    def stop(self):
        pm = self.prefab.system.processManager.get()
        pm.stop('portal')

    def set_admin_password(self, passwd):
        # wait for the admin user to be created by portal
        timeout = 60
        start = time.time()
        resp = self.prefab.core.run('jsuser list', showout=False)[1]
        while resp.find('admin') == -1 and start + timeout > time.time():
            try:
                time.sleep(2)
                resp = self.prefab.core.run('jsuser list', showout=False)[1]
            except BaseException:
                continue

        if resp.find('admin') == -1:
            self.prefab.core.run('jsuser add --data admin:%s:admin:admin@mail.com:cockpit' % passwd)
        else:
            self.prefab.core.run('jsuser passwd -ul admin -up %s' % passwd)
