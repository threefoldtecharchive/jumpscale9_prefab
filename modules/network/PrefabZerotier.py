from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZerotier(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/zerotier/")
        if "LEDE" in self.prefab.platformtype.osname:
            self.CLI = 'zerotier-cli'
        else:
            self.CLI = j.sal.fs.joinPaths(self.prefab.core.dir_paths['BINDIR'], 'zerotier-cli')


    def reset(self):
        super().reset()
        self.core.dir_remove(self.BUILDDIRL)
        self._init()
        self.doneDelete("build")

    def build(self, reset=False, install=True):

        if reset:
            self.reset()

        if self.doneGet("build") and not reset:
            return

        if "LEDE" in self.prefab.platformtype.osname:
            self.prefab.core.run("opkg install zerotier")
            self.doneSet("build")
            return

        if self.prefab.core.isMac:
            if not self.doneGet("xcode_install"):
                self.prefab.core.run("xcode-select --install", die=False, showout=True)
                self.doneSet("xcode_install")
        elif self.prefab.core.isUbuntu:
            self.prefab.system.package.ensure("gcc")
            self.prefab.system.package.ensure("g++")
            self.prefab.system.package.ensure('make')

        codedir = self.prefab.tools.git.pullRepo(
            "https://github.com/zerotier/ZeroTierOne", reset=reset, depth=1, branch='master')

        cmd = "cd {code} && DESTDIR={build} make one".format(code=codedir, build=self.BUILDDIRL)
        self.prefab.core.run(cmd)
        self.prefab.core.dir_ensure(self.BUILDDIRL)
        cmd = "cd {code} && DESTDIR={build} make install".format(code=codedir, build=self.BUILDDIRL)
        self.prefab.core.run(cmd)

        self.doneSet("build")
        if install:
            self.install()

    def install(self):
        if not self.doneGet("build"):
            self.build(install=False)
        if "LEDE" in self.prefab.platformtype.osname:
            return
        bindir = self.prefab.core.dir_paths['BINDIR']
        self.prefab.core.dir_ensure(bindir)
        for item in self.prefab.core.find(j.sal.fs.joinPaths(self.BUILDDIRL, 'usr/sbin')):
            self.prefab.core.file_copy(item, bindir + '/')

    def start(self):
        self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("$BINDIR"))
        self.prefab.bash.profileDefault.save()
        pm = self.prefab.system.processmanager.get()
        pm.ensure('zerotier-one', cmd='zerotier-one')

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop('zerotier-one')

    def join_network(self, network_id):
        """
        join the netowrk identied by network_id
        """
        cmd = '{cli} join {id}'.format(cli=self.CLI, id=network_id)
        rc, out, err = self.prefab.core.run(cmd, die=False)
        if rc != 0 or out.find('OK') == -1:
            raise j.exceptions.RuntimeError("error while joinning network: \n{}".format(err))

    def leave_network(self, network_id):
        """
        leave the netowrk identied by network_id
        """
        cmd = '{cli} leave {id}'.format(cli=self.CLI, id=network_id)
        rc, out, _ = self.prefab.core.run(cmd, die=False)
        if rc != 0 or out.find('OK') == -1:
            error_msg = "error while joinning network: "
            if out.find("404") != -1:
                error_msg += 'not part of the network {}'.format(network_id)
            else:
                error_msg += out
            raise j.exceptions.RuntimeError(error_msg)

    def list_networks(self):
        """
        list all joined networks.
        return a list of dict
        network = {
            'network_id': ,
            'name': ,
            'mac': ,
            'status': ,
            'type': ,
            'dev': ,
            'ips': ,
        }
        """
        cmd = '{cli} listnetworks'.format(cli=self.CLI)
        rc, out, _ = self.prefab.core.run(cmd, die=False)
        if rc != 0:
            raise j.exceptions.RuntimeError(out)

        lines = out.splitlines()
        if len(lines) < 2:
            return {}

        networks = []
        for line in out.splitlines()[1:]:
            ss = line.split(' ')
            network = {
                'network_id': ss[2],
                'name': ss[3],
                'mac': ss[4],
                'status': ss[5],
                'type': ss[6],
                'dev': ss[7],
                'ips': ss[8].split(','),
            }
            networks.append(network)

        return networks

    def list_peers(self):
        """
        list connected peers.
        return a list of dict
        network = {
            'ztaddr': ,
            'paths': ,
            'latency': ,
            'version': ,
            'role': ,
        }
        """
        cmd = '{cli} listpeers'.format(cli=self.CLI)
        rc, out, _ = self.prefab.core.run(cmd, die=False)
        if rc != 0:
            raise j.exceptions.RuntimeError(out)

        lines = out.splitlines()
        if len(lines) < 2:
            return {}

        peers = []
        for line in out.splitlines()[1:]:
            ss = line.split(' ')
            peer = {
                'ztaddr': ss[2],
                'paths': ss[3],
                'latency': ss[4],
                'version': ss[5],
                'role': ss[6],
            }
            peers.append(peer)

        return peers
