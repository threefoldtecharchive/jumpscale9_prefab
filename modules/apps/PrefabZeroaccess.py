from jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabZeroaccess(app):
    NAME = "zeroaccess"

    def _init(self):
        self.zeroaccess_dir = self.replace("$CODEDIR/github/0-complexity/0-access")
        self.git_url = "https://github.com/0-complexity/0-access.git"

    def build(self, reset=False):
        if self.doneCheck('build', reset):
            return

        # Install jumpscale
        self.prefab.jumpscale.jumpscalecore.install()

        # Clone the repository
        self.prefab.tools.git.pullRepo(self.git_url, dest=self.zeroaccess_dir)
        self.doneSet('build')

    def install(self, reset=False):
        self.build(reset=reset)

        # Install 0-access
        self.prefab.core.run('cd {} && pip3 install -r requirements.txt'.format(self.zeroaccess_dir))
        self.prefab.system.ssh.keygen(name="id_rsa")
        self.prefab.core.run("""
        cp {zeroaccess_path}/lash /bin 
        chmod 755 /bin/lash
        mkdir -p /var/recordings/index
        chmod -R 777 /var/recordings
        mkdir -p /var/run/sshd
        """.format(zeroaccess_path=self.zeroaccess_dir))

    def start(self, organization, client_secret, uri, port, ssh_ip, ssh_port,
              gateone_url=None, session_timeout=600):
        self.stop()
        cmd = "python3 0-access.py {organization} {client_secret} {uri} {port} {ssh_ip} {ssh_port} {session_timeout}"
        cmd = cmd.format(
            organization=organization,
            client_secret=client_secret,
            uri=uri,
            port=port,
            ssh_ip=ssh_ip,
            ssh_port=ssh_port,
            session_timeout=session_timeout
        )
        if gateone_url:
            cmd += " --gateone-url {}".format(gateone_url)
        self.prefab.system.processmanager.get().ensure("zeroaccess", cmd, path=self.zeroaccess_dir,
                                                       wait=10, expect="sshd")

    def stop(self):
        self.prefab.system.processmanager.get().stop("zeroaccess")
