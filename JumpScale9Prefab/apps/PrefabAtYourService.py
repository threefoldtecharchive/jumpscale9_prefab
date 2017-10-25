from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabAtYourService(base):
    def _init(self):
        self.base_dir = j.sal.fs.joinPaths(
            self.prefab.core.dir_paths["JSAPPSDIR"],
            "atyourservice"
        )

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
        j.application.config['ays'] = ays_config
        j.core.state.configSave()

    def get_code(self):
        """
        Pull the ays repo if doesnt exist
        """
        branch = self.prefab.bash.env.get('JS9BRANCH', 'master')
        self.logger.info("Get ays code on branch:'%s'" % branch)
        self.prefab.development.git.pullRepo("https://github.com/Jumpscale/ays9.git", branch=branch)

    def load_ays_space(self, install_portal=False):
        """
        add ays space to portal
        """
        code_dir = self.prefab.core.dir_paths["CODEDIR"]
        if install_portal:
            self.prefab.apps.portal.install()
        if j.sal.fs.exists('{}/portals'.format(self.prefab.core.dir_paths["JSAPPSDIR"])):
            self.prefab.apps.portal.addSpace('{}/github/jumpscale/ays9/apps/AYS'.format(code_dir))
            self.prefab.apps.portal.addActor('{}/github/jumpscale/ays9/apps/ays__tools'.format(code_dir))

    def install(self, install_portal=False):
        self.prefab.core.dir_ensure(self.base_dir)
        server_dir = j.sal.fs.joinPaths(self.base_dir, 'JumpScale9AYS/ays/server/')
        self.prefab.core.dir_ensure(server_dir)
        code_dir = self.prefab.core.dir_paths["CODEDIR"]
        self.get_code()
        # link apidocs and index.html
        self.prefab.core.file_link(
            j.sal.fs.joinPaths(code_dir, 'github/jumpscale/ays9/JumpScale9AYS/ays/server/apidocs'),
            j.sal.fs.joinPaths(server_dir, 'apidocs')
        )

        self.prefab.core.file_link(
            j.sal.fs.joinPaths(code_dir, 'github/jumpscale/ays9/JumpScale9AYS/ays/server/index.html'),
            j.sal.fs.joinPaths(self.base_dir, 'JumpScale9AYS/ays/server/index.html')
        )

        self.prefab.core.file_link(
            j.sal.fs.joinPaths(code_dir, 'github/jumpscale/ays9/main.py'),
            j.sal.fs.joinPaths(self.base_dir, 'main.py')
        )
        self.load_ays_space(install_portal)

    def start(self, host='localhost', port=5000, log='info', dev=False):
        cmd = 'cd {base_dir}; python3 main.py -h {host} -p {port} --log {log}'.format(base_dir=self.base_dir,
                                                                                      host=host, port=port, log=log)
        if dev:
            cmd += " --dev "
        self.prefab.processmanager.ensure(name='atyourservice', cmd=cmd)

    def stop(self):
        self.prefab.processmanager.stop(name='atyourservice')
