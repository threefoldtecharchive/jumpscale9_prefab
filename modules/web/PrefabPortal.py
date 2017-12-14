from js9 import j
import time
import os
import pytoml


base = j.tools.prefab._getBaseClass()


class PrefabPortal(base):

    def _init(self):
        self.portal_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths["JSAPPSDIR"], "portals/")

    def configure(
            self,
            mongodbip="127.0.0.1",
            mongoport=27017,
            production=True,
            client_id='',
            client_secret='',
            organization='',
            redirect_address='',
            name='main'):

        cfg = self.prefab.executor.state.configGet('portal')
        cfg[name]['production'] = production

        if production:
            oauth_cfg = cfg[name]['oauth']
            oauth_cfg['client_id'] = client_id
            oauth_cfg['client_scope'] = 'user:email:main,user:memberof:%s' % client_id
            oauth_cfg['client_secret'] = client_secret
            oauth_cfg['force_oauth_instance'] = 'itsyou.online'
            oauth_cfg['default_groups'] = ['admin', 'user']
            oauth_cfg['organization'] = organization
            oauth_cfg['redirect_url'] = 'http://%s/restmachine/system/oauth/authorize' % redirect_address

        cfg[name]['mongoengine'] = {'host': mongodbip, 'port': mongoport}
        self.executor.state.configSet('portal', cfg, save=True)

    def add_configuration(self, config_dict, name="main"):
        """
        use this method when ever u want to add some config to portal
        usually when u add a new space
        """
        cfg = self.prefab.executor.state.configGet('portal')
        for key, value in config_dict.items():
            cfg[name][key] = value
        self.prefab.executor.state.configSet('portal',cfg)

    def install(self, start=True, branch='master', reset=False, name="main", port='8200', ip='127.0.0.1'):
        """
        grafanaip and port should be the external ip of the machine
        Portal install will only install the portal and libs. No spaces but the system ones will be add by default.
        To add spaces and actors, please use addSpace and addactor
        """
        self.logger.info("Install prefab portal on branch:'%s'" % branch)
        self.prefab.core.dir_ensure(j.sal.fs.joinPaths(self.portal_dir, name))
        self.prefab.bash.fixlocale()
        if not reset and self.doneGet("install-"+name):
            self.linkCode(name=name)
            if start:
                self.start(name=name)
            return

        self.prefab.db.mongodb.install()
        self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("$BINDIR"))
        self.prefab.bash.profileDefault.save()

        # install the dependencies if required
        self.getcode(branch=branch)
        self.installDeps(reset=reset, name=name)

        # pull repo with required branch ; then link dirs and files in required places
        self.linkCode(name=name)
        portal_config_path = '%s/github/jumpscale/portal9/apps/portalbase/config.toml' % self.prefab.core.dir_paths["CODEDIR"]
        portal_config_data = self.prefab.core.file_read(portal_config_path)
        portal_config_data = portal_config_data.format(name=name, port=port, ip=ip)
        portal_config = pytoml.loads(portal_config_data)

        cvg = self.prefab.executor.state.configGet('portal')
        cvg[name] = portal_config['portal'][name]
        self.prefab.executor.state.configSet('portal', cvg)

        if start:
            self.start(name=name)

        self.doneSet("install-"+name)

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

    def installDeps(self, reset=False, name="main"):
        """
        make sure new env arguments are understood on platform
        """
        if not reset and self.doneGet("installdeps"+name):
            return

        if "darwin" not in self.prefab.platformtype.osname:
            self.prefab.system.package.ensure('build-essential')
            self.prefab.system.package.ensure('libssl-dev')
            self.prefab.system.package.ensure('libffi-dev')
            self.prefab.system.package.ensure('python3-dev')

        if "darwin" in self.prefab.platformtype.osname:
            self.prefab.system.package.install(['libtiff', 'libjpeg', 'webp', 'little-cms2', 'snappy'])
            self.prefab.core.run('CPPFLAGS="-I/usr/local/include -L/usr/local/lib" pip3 install python-snappy')
        else:
            self.prefab.system.package.install(['libjpeg-dev', 'libffi-dev', 'zlib1g-dev'])

        # snappy install
        if "darwin" not in self.prefab.platformtype.osname:
            self.prefab.system.package.ensure('libsnappy-dev')
            self.prefab.system.package.ensure('libsnappy1v5')
            self.prefab.runtimes.pip.install('python-snappy')

        cmd = """
            cd {CODEDIR}/github/jumpscale/portal9
            pip3 install -e .
            """.format(CODEDIR=self.prefab.core.dir_paths["CODEDIR"])
        self.prefab.core.execute_bash(cmd)
        self.doneSet("installdeps"+name)

    def getcode(self, branch='master'):
        self.logger.info("Get portal code on branch:'%s'" % branch)
        if branch == "":
            branch = os.environ.get('JS9BRANCH')
        self.prefab.tools.git.pullRepo(
            "https://github.com/Jumpscale/portal9.git", branch=branch, ignorelocalchanges=False)

    def linkCode(self, name="main"):

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

        self.prefab.core.dir_ensure(j.sal.fs.joinPaths(self.portal_dir, name))

        self.prefab.core.dir_ensure('%s/base/' % j.sal.fs.joinPaths(self.portal_dir, name))

        self.prefab.core.dir_ensure("$CFGDIR/portals/"+name+"/")
        # copy portal_start.py
        self.prefab.core.file_copy(
            j.sal.fs.joinPaths(
                CODE_DIR,
                'github/jumpscale/portal9/apps/portalbase/portal_start.py'),
            j.sal.fs.joinPaths(self.portal_dir, name))
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
                self.prefab.core.file_link(source=space, destination='$JSAPPSDIR/portals/'+name+'/base/%s' % space_name)

    def addSpace(self, spacepath, name='main'):
        spacename = j.sal.fs.getBaseName(spacepath)
        dest_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths[
            'JSAPPSDIR'], 'portals', name, 'base', spacename)
        self.prefab.core.file_link(spacepath, dest_dir)

    def addActor(self, actorpath, name='main'):
        actorname = j.sal.fs.getBaseName(actorpath)
        dest_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths[
            'JSAPPSDIR'], 'portals', name, 'base', actorname)
        self.prefab.core.file_link(actorpath, dest_dir)

    def start(self, passwd=None, name='main'):
        """
        Start the portal
        passwd : if not None, change the admin password to passwd after start
        """
        self.prefab.db.mongodb.start()
        cmd = "python3 portal_start.py --instance "+name
        pm = self.prefab.system.processmanager.get()
        pm.ensure('portal-'+name, cmd=cmd, path=j.sal.fs.joinPaths(self.portal_dir, name))

        if passwd is not None:
            self.set_admin_password(j.sal.unix.crypt(passwd))

    def stop(self, name='main'):
        pm = self.prefab.system.processmanager.get()
        pm.stop('portal-'+name)

    def set_admin_password(self, passwd):
        admin = j.portal.tools.usermanager.getUser("admin")

        if not admin:
            j.portal.tools.usermanager.createUser("admin", passwd, "admin@mail.com", "admin")
        else:
            admin.update(passwd=passwd)
