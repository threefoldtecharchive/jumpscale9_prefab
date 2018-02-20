from js9 import j
import time
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
        self.start()
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
        #install golang dependency
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
        url  = 'https://github.com/gravitational/teleport/releases/download/{0}/teleport-{0}-linux-amd64-bin.tar.gz'.format(version)
        self.prefab.core.file_download(url, '$TMPDIR/teleport.tar.gz')
        self.prefab.core.run('tar -xzf $TMPDIR/teleport.tar.gz -C $TMPDIR')
        self.prefab.core.file_copy('$TMPDIR/teleport/teleport', '$BINDIR')
        self.prefab.core.file_copy('$TMPDIR/teleport/tsh', '$BINDIR')
        self.prefab.core.file_copy('$TMPDIR/teleport/tctl', '$BINDIR')
        for path in extra_paths:
            self.prefab.core.file_copy('$TMPDIR/teleport/teleport', path)
            self.prefab.core.file_copy('$TMPDIR/teleport/tsh', path)
            self.prefab.core.file_copy('$TMPDIR/teleport/tctl', path)

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
        self.prefab.core.file_copy('%s/build/teleport' % self.REPOPATH, '$BINDIR')
        self.prefab.core.file_copy('%s/build/tsh' % self.REPOPATH, '$BINDIR')
        self.prefab.core.file_copy('%s/build/tctl' % self.REPOPATH, '$BINDIR')
        for path in extra_paths:
            self.prefab.core.file_copy('%s/build/teleport' % self.REPOPATH, path)
            self.prefab.core.file_copy('%s/build/tsh' % self.REPOPATH, path)
            self.prefab.core.file_copy('%s/build/tctl' % self.REPOPATH, path)
        
        self.doneSet('install')

    def write_config(self, name='main', trusted_clusters=[]):
        """
        write configuration file
        
        @param name ,, str cluster name to be used has to be the same if going to connect to existing cluster
        @param trusted_cluster_paths,, list(dict(cluster)) has to be in the format:
        cluster = {
                'key': trusted_cluster_key
                'allow_logins': trusted_cluster_logins
                'tunnel_addr': trusted_cluster_addr
                'name': trusted_cluster_name
            }
        """
        #configure
        self.CONFIG['auth_service']['cluster_name'] = name
        for cluster in trusted_clusters:
            for key in cluster:
                if key not in ('key', 'allow_logins', 'tunnel_addr', 'name'):
                    raise RuntimeError('key is not suppported %s' % key)
            cluster['key_file'] = '/var/lib/teleport/%s' % cluster.pop('name')
            from pprint import pprint ; from IPython import embed ; import ipdb ; ipdb.set_trace()
            self.prefab.core.file_write(cluster['key_file'], cluster.pop('key'))
        self.CONFIG['auth_service']['trusted_clusters'] = trusted_clusters
        self.prefab.core.file_write('/etc/teleport.yaml', j.data.serializer.yaml.dumps(self.CONFIG))

  
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
                "organization": org_name ,
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
        self.prefab.core.file_write('$TMPDIR/github.yaml', j.data.serializer.yaml.dumps(self.GITHUB_DATA))
        timer = 20
        while not self.prefab.core.file_exists("/var/lib/teleport/host_uuid"):
            timer -= 1
            time.sleep(1)
            if timer == 0:
                raise RuntimeError("teleport could not be reached")
        self.prefab.core.run('tctl create $TMPDIR/github.yaml')
        
    def start(self,cmd="$BINDIR/teleport start"):
        """
        Start the teleport service.
        """
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='teleport', cmd=cmd)

    def stop(self):
        """
        Stop the teleport service.
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop('teleport')

    def restart(self):
        """
        restart the teleport service.
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop("teleport")
        self.start()

