from Jumpscale import j
import time
import uuid
app = j.tools.prefab._getBaseAppClass()


class PrefabTeleport(app):
    NAME = "teleport"

    def _init(self):
        self._cluster_params = None
        self.REPOPATH = '$GOPATH/src/github.com/gravitational/teleport'
        self.CONFIG = {
            "auth_service": {
                "enabled": "yes",
                "authentication": {
                    "type": "github"
                }
            },
            "proxy_service": {
                "enabled": "yes",
                "listen_addr": "0.0.0.0:3023",
                "tunnel_listen_addr": "0.0.0.0:3024",
                "web_listen_addr": "0.0.0.0:3080"
            }
        }
        self.GITHUB_DATA = {
            "kind": "github",
            "version": "v3",
            "metadata": {
                "name": "github"
            }
        }

    def full_setup(self, client_secret, client_id, teams, exposed_ip, name='github', logins=['root'], reset=False, dev=False):
        """
        Will build, install, configure, and start teleport 
        """
        if self.doneCheck("full_setup", reset):
            return
        if not dev:
            self.package_install()
        else:
            self.build(reset=reset)
            self.install(reset=reset)
        self.write_config()
        self.start(insecure=True)
        self.apply_permissions(client_secret, client_id, teams, exposed_ip, name, logins)
        self.doneSet('full_setup')

    def build(self, reset=False):
        """
        Builds the binaries for teleport.
        The Go compiler is somewhat sensitive to amount of memory: you will need at least 1GB of virtual memory to compile Teleport.
        512MB instance without swap will not work.
        """
        if self.doneCheck("build", reset):
            return
        # install golang dependency
        self.prefab.runtimes.golang.install()

        # get repo
        self.prefab.runtimes.golang.get('github.com/gravitational/teleport', install=False)
        # build binary
        self.prefab.core.run('cd %s && make full' % self.REPOPATH)
        self.doneSet('build')

    def package_install(self,  extra_paths=[], version='v2.4.1'):
        """
        download the binaries directly and install , this used for production env for less dependencies and space allocation.

        @param extra_paths,,str extra paths to copy the binaries into 
        @param version,, version of the binaries to download
        """
        url = 'https://github.com/gravitational/teleport/releases/download/{0}/teleport-{0}-linux-amd64-bin.tar.gz'.format(version)
        self.prefab.core.file_download(url, '{DIR_TEMP}/teleport.tar.gz')
        self.prefab.core.run('tar -xzf {DIR_TEMP}/teleport.tar.gz -C {DIR_TEMP}')
        self.prefab.core.file_copy('{DIR_TEMP}/teleport/teleport', '{DIR_BIN}')
        self.prefab.core.file_copy('{DIR_TEMP}/teleport/tsh', '{DIR_BIN}')
        self.prefab.core.file_copy('{DIR_TEMP}/teleport/tctl', '{DIR_BIN}')
        for path in extra_paths:
            self.prefab.core.file_copy('{DIR_TEMP}/teleport/teleport', path)
            self.prefab.core.file_copy('{DIR_TEMP}/teleport/tsh', path)
            self.prefab.core.file_copy('{DIR_TEMP}/teleport/tctl', path)

    def install(self, extra_paths=[], reset=False):
        """
        Moves the binaries into the required $BINDDIR
        @param extra_paths,,str extra paths to copy the binaries into 
        @param reset,, bool used to redo this command 
        """
        if self.doneCheck("install", reset):
            return
        # create the default data directory before starting:
        self.prefab.core.dir_ensure('/var/lib/teleport')
        # move binaries to correct location
        self.prefab.core.file_copy('%s/build/teleport' % self.REPOPATH, '{DIR_BIN}')
        self.prefab.core.file_copy('%s/build/tsh' % self.REPOPATH, '{DIR_BIN}')
        self.prefab.core.file_copy('%s/build/tctl' % self.REPOPATH, '{DIR_BIN}')
        for path in extra_paths:
            self.prefab.core.file_copy('%s/build/teleport' % self.REPOPATH, path)
            self.prefab.core.file_copy('%s/build/tsh' % self.REPOPATH, path)
            self.prefab.core.file_copy('%s/build/tctl' % self.REPOPATH, path)

        self.doneSet('install')

    def write_config(self, name='main', key_path=None, cert_path=None):
        """
        write configuration file

        @param name ,, str cluster name to be used has to be the same if going to connect to existing cluster
        @param trusted_cluster_paths,, list(dict(cluster)) has to be in the format:

        """
        # configure
        self.CONFIG['auth_service']['cluster_name'] = name
        self.CONFIG['auth_service']['tokens'] = ['trusted_cluster:%s' % j.data.hash.sha256_string(name)]
        if key_path and cert_path:
            self.CONFIG['proxy_service']['https_key_file'] = key_path
            self.CONFIG['proxy_service']['https_cert_file'] = cert_path 
        self.prefab.core.file_write('/etc/teleport.yaml', j.data.serializers.yaml.dumps(self.CONFIG))

    def apply_trusted_cluster(self, name, token, web_proxy_addr, tunnel_addr):
        """
        write and apply the trusted cluster resource

        @param name ,, str name of the trusted cluster need to be the same name in the config file of the dsestination
        @param token,, str the token in the destination config file
        @param web_proxy_addr,, str the exposed ip for the instance
        @param tunnel_addr,, str the exposed ip for the instance
        """
        trusted_cluster_config = {"kind": "trusted_cluster", "version": "v2"}
        spec = {
            "enabled": True,
            "token": j.data.hash.sha256_string(name),
            "tunnel_addr": tunnel_addr,  # usually on port 3024
            "web_proxy_addr": web_proxy_addr  # usually on port  3080
        }
        trusted_cluster_config['spec'] = spec
        trusted_cluster_config['metadata'] = {'name': name}
        self.prefab.core.file_write('{DIR_TEMP}/cluster_%s.yaml' %
                                    name, j.data.serializers.yaml.dumps(trusted_cluster_config))
        self.prefab.core.run('tctl create {DIR_TEMP}/cluster_%s.yaml' % name)

    @property
    def cluster_params(self):
        """
        The command used for a node to join a teleport cluster
        """
        if not self._cluster_params:
            self._cluster_params = self.prefab.core.run('tctl nodes add')
        return self._cluster_params

    def apply_permissions(self, client_secret, client_id, teams, exposed_ip, name='github', logins=['root']):
        """
        adds a new github authorization module with organization and team should runs after teleport start

        @param client_secret,, str the github secert used for oauth 
        @param client_id,, str  the gihub id used for oauth
        @param teams,, list(str('organization/team'))  the teams and organization to be used
        @param expose_ip,, the ip used to construct the redirect url must be accessible from the place it was called
        @param logins,, list(str) list of usernames to give login , will default to root. 
        """
        team_configs_list = []
        for team in teams:
            org_name, team_name = team.split('/')
        team_configs_list.append({
            "organization": org_name,
            "team": team_name,
            "logins": logins
        })
        spec = {
            "client_id": client_id,
            "client_secret": client_secret,
            "display": "Github",
            "redirect_url": "https://%s:3080/v1/webapi/github/callback" % exposed_ip,
            "teams_to_logins": team_configs_list
        }
        self.GITHUB_DATA['spec'] = spec
        self.GITHUB_DATA['metadata']['name'] = name
        self.prefab.core.file_write('{DIR_TEMP}/github.yaml', j.data.serializers.yaml.dumps(self.GITHUB_DATA))
        timer = 20
        while not self.prefab.core.file_exists("/var/lib/teleport/host_uuid"):
            timer -= 1
            time.sleep(1)
            if timer == 0:
                raise RuntimeError("teleport could not be reached")
        self.prefab.core.run('tctl create {DIR_TEMP}/github.yaml')

    def start(self, cmd="{DIR_BIN}/teleport start", insecure=False):
        """
        Start the teleport service.
        """
        if insecure:
            cmd += ' --insecure'
        pm = self.prefab.system.processmanager.get('systemd')
        pm.ensure(name='teleport', cmd=cmd)

    def stop(self):
        """
        Stop the teleport service.
        """
        pm = self.prefab.system.processmanager.get('systemd')
        pm.stop('teleport')

    def restart(self):
        """
        restart the teleport service.
        """
        pm = self.prefab.system.processmanager.get('systemd')
        pm.stop("teleport")
        self.start()
