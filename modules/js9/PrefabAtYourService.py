from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabAtYourService(base):
    def _init(self):
        self.base_dir = j.sal.fs.joinPaths(
            self.prefab.core.dir_paths["JSAPPSDIR"],
            "atyourservice"
        )
        self.repo_dir = j.sal.fs.joinPaths(self.prefab.core.dir_paths["CODEDIR"], 'github/jumpscale/ays9/')

    def configure(self, production=False, client_secret='', client_id='', organization='', redirect_address='locahost:5000'):
        jwt_key = "MHYwEAYHKoZIzj0CAQYFK4EEACIDYgAES5X8XrfKdx9gYayFITc89wad4usrk0n27MjiGYvqalizeSWTHEpnd7oea9IQ8T5oJjMVH5cc0H5tFSKilFFeh//wngxIyny66+Vq5t5B0V0Ehy01+2ceEon2Y0XDkIKv"
        ays_config = {
            'production': production,
            'oauth': {
                'jwt_key': jwt_key,
                'client_secret': client_secret,
                'redirect_uri': "https://{}".format(redirect_address),
                'client_id': client_id,
                'organization': organization
            }
        }
        self.executor.state.configSet('ays', ays_config, save=True)

    def configure_portal(self, host="http://localhost", port="5000", portal="main"):
        if not host.startswith('http'):
            host = "http://%s" % host
        config = {"ays_uri": "%s:%s" % (host, port)}
        self.prefab.web.portal.add_configuration(config)
        nav_path = "$JSAPPSDIR/portals/{portal}/base/AYS/.space/nav.wiki".format(portal=portal)
        nav = self.prefab.core.file_read(nav_path).format(ays_uri="%s:%s" % (host, port))
        self.prefab.core.file_write(nav_path, nav)
        self.prefab.web.portal.stop()
        self.prefab.web.portal.start()

    def get_code(self, branch):
        """
        Pull the ays repo if doesnt exist
        """
        if not branch:
            branch = self.prefab.bash.env.get('JS9BRANCH', 'master')
        self.logger.info("Get ays code on branch:'%s'" % branch)
        self.prefab.development.git.pullRepo("https://github.com/Jumpscale/ays9.git", branch=branch)

    def load_ays_space(self, install_portal=False):
        """
        add ays space to portal
        """
        code_dir = self.prefab.core.dir_paths["CODEDIR"]
        if install_portal:
            self.prefab.web.portal.install(reset=True)
        if j.sal.fs.exists('{}/portals'.format(self.prefab.core.dir_paths["JSAPPSDIR"])):
            self.prefab.web.portal.addSpace('{}/github/jumpscale/ays9/apps/AYS'.format(code_dir))
            self.prefab.web.portal.addActor('{}/github/jumpscale/ays9/apps/ays__tools'.format(code_dir))

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
        self.load_ays_space(install_portal)

    def start(self, host='127.0.0.1', port=5000, log='info', dev=False):
        """
        Starts an AYS instance
        """
        # check if the install was called before
        if not j.sal.fs.exists(j.sal.fs.joinPaths(self.base_dir, 'main.py')):
            self.logger.warning('AYS is not installed. Installing it...')
            self.install()
            
        cmd = 'cd {base_dir}; python3 main.py -h {host} -p {port} --log {log}'.format(base_dir=self.base_dir,
                                                                                      host=host, port=port, log=log)
        if dev:
            cmd += " --dev "
        self.prefab.processmanager.ensure(name='atyourservice', cmd=cmd)

    def stop(self):
        self.prefab.processmanager.stop(name='atyourservice')