from js9 import j
import re

base = j.tools.prefab._getBaseClass()


class PrefabAtYourService(base):
    def _init(self):
        self.base_dir = j.sal.fs.joinPaths(
            self.prefab.core.dir_paths["JSAPPSDIR"],
            "atyourservice"
        )
        self.repo_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths["CODEDIR"], 'github/jumpscale/ays9/')

    def configure(self, production=False, organization='', restart=True, host='127.0.0.1', port=5000):
        jwt_key = "MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n27MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny66+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv"
        ays_config = {
            'production': production,
            'oauth': {
                'jwt_key': jwt_key,
                'organization': organization
            },
            'host': host,
            'port': port
        }
        rediskwargs = j.core.db.config_get('unixsocket')
        if not rediskwargs['unixsocket']:
            dbkwargs = j.core.db.connection_pool.connection_kwargs
            rediskwargs = {'host': dbkwargs['host'], 'port': dbkwargs['port']}
        ays_config.update({'redis': rediskwargs})

        self.executor.state.configSet('ays', ays_config, save=True)
        if restart:
            self.stop()
            self.start()

    def configure_portal(self, ays_url='http://localhost:5000', ays_console_url='', portal_name='main', restart=True):
        """Configure AYS in portal

         Allows the user to configure AYS in portal

        Keyword Arguments:
            ays_url {string} -- ays api full url (default: {"http://localhost:5000"})
            ays_console_url {string} -- ays api console full url (default: {<ays_url>})
            portal_name {string} -- portal instance name (default: {"main"})
        """

        if not ays_url.startswith('http'):
            ays_url = "http://%s" % ays_url
        config = {
            'ays_uri': ays_url,
        }
        console_url = ays_console_url or ays_url
        self.prefab.web.portal.add_configuration(config)
        nav_path = '$JSAPPSDIR/portals/{portal}/base/AYS/.space/nav.wiki'.format(portal=portal_name)
        nav = self.prefab.core.file_read(nav_path)
        nav = re.sub(r'AYS API:.*', r'AYS API:{}/apidocs/index.html?raml=api.raml'.format(console_url), nav)
        self.prefab.core.file_write(nav_path, nav)
        if restart:
            self.prefab.web.portal.stop(name=portal_name)
            self.prefab.web.portal.start(name=portal_name)

    def configure_api_console(self, url="http://localhost:5000"):
        """Configure AYS API Console

         Allows the user to configure AYS API Console with desired host and port

        Keyword Arguments:
            url {string} -- desired ays console api binding (default: {"http://localhost:5000"})
        """

        raml_path = "$JSAPPSDIR/atyourservice/JumpScale9AYS/ays/server/apidocs/api.raml"
        raml = self.prefab.core.file_read(raml_path)

        raml = re.sub(
            r'baseUri: .*',
            r'baseUri: %s' % url,
            raml
        )
        self.prefab.core.file_write(raml_path, raml)

    def get_code(self, branch):
        if not branch:
            branch = self.prefab.bash.env.get('JS9BRANCH', 'master')
        self.logger.info("Get ays code on branch:'%s'" % branch)
        self.prefab.tools.git.pullRepo("https://github.com/Jumpscale/ays9.git", branch=branch)

    def load_ays_space(self, install_portal=False, branch="master"):
        """
        add ays space to portal
        """
        # make sure to have ays repo files locally even if you will connect the portal with a remote ays server
        # to get ays app files
        self.get_code(branch=branch)
        if install_portal:
            self.prefab.web.portal.install()
        if self.core.file_exists('{}/portals'.format(self.prefab.core.dir_paths["JSAPPSDIR"])):
            self.prefab.web.portal.addSpace('{}apps/AYS'.format(self.repo_dir))
            self.prefab.web.portal.addActor('{}apps/ays__tools'.format(self.repo_dir))

    def install_pip_package(self):
        """
        install the pip packages for ays
        """
        cmd = 'cd %s && pip3 install -e .' % self.repo_dir
        self.prefab.core.run(cmd)

    def install(self, install_portal=False, branch=None):
        self.prefab.core.dir_ensure(self.base_dir)
        server_dir = j.sal.fs.joinPaths(self.base_dir, 'JumpScale9AYS/ays/server/')
        self.prefab.core.dir_ensure(server_dir)
        self.get_code(branch)
        self.install_pip_package()
        # link apidocs and index.html
        self.prefab.core.file_link(
            j.sal.fs.joinPaths(self.repo_dir, 'JumpScale9AYS/ays/server/apidocs'),
            j.sal.fs.joinPaths(server_dir, 'apidocs')
        )

        self.prefab.core.file_link(
            j.sal.fs.joinPaths(self.repo_dir, 'JumpScale9AYS/ays/server/index.html'),
            j.sal.fs.joinPaths(self.base_dir, 'JumpScale9AYS/ays/server/index.html')
        )

        self.prefab.core.file_link(
            j.sal.fs.joinPaths(self.repo_dir, 'main.py'),
            j.sal.fs.joinPaths(self.base_dir, 'main.py')
        )
        self.load_ays_space(install_portal, branch=branch)

    def start(self, log='info', dev=False):
        """
        Starts an AYS instance
        Please configure first
        """
        # check if the install was called before
        if not self.prefab.core.exists(j.sal.fs.joinPaths(self.base_dir, 'main.py')):
            self.logger.warning('AYS is not installed. Installing it...')
            self.install()

        try:
            j.core.state.configGet('ays')
        except j.exceptions.Input:
            self.logger.warning('AYS has not been configured. Will start with default host:127.0.0.1 and port:5000')

        cfg = self.executor.state.configGet('ays', {'host': '127.0.0.1', 'port': 5000}, set=True)
        cmd = 'cd {base_dir}; python3 main.py -h {host} -p {port} --log {log}'.format(base_dir=self.base_dir,
                                                                                      host=cfg['host'], port=cfg['port'], log=log)
        if dev:
            cmd += " --dev "
        pm = self.prefab.system.processmanager.get()
        pm.ensure('atyourservice', cmd=cmd)

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop(name='atyourservice')
