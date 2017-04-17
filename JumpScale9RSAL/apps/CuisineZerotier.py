from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineZerotier(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/zerotier/")
        self.CLI = j.sal.fs.joinPaths(self.cuisine.core.dir_paths['BINDIR'], 'zerotier-cli')

    def reset(self):
        self.core.dir_remove(self.BUILDDIRL)

    def build(self, reset=False, install=True):
        if reset:
            self.reset()

        if self.doneGet("build") and not reset:
            return

        if self.cuisine.core.isMac:
            if not self.doneGet("xcode_install"):
                self.cuisine.core.run("xcode-select --install", die=False, showout=True)
                self.doneSet("xcode_install")
        elif self.cuisine.core.isUbuntu:
            self.cuisine.package.ensure("gcc")
            self.cuisine.package.ensure("g++")
            self.cuisine.package.ensure('make')

        codedir = self.cuisine.development.git.pullRepo(
            "https://github.com/zerotier/ZeroTierOne", reset=reset, depth=1, branch='1.1.14')

        cmd = "cd {code} && DESTDIR={build} make one".format(code=codedir, build=self.BUILDDIRL)
        self.cuisine.core.run(cmd)
        self.cuisine.core.dir_ensure(self.BUILDDIRL)
        cmd = "cd {code} && DESTDIR={build} make install".format(code=codedir, build=self.BUILDDIRL)
        self.cuisine.core.run(cmd)

        self.doneSet("build")
        if install:
            self.install()

    def install(self):
        bindir = self.cuisine.core.dir_paths['BINDIR']
        self.cuisine.core.dir_ensure(bindir)
        for item in self.cuisine.core.find(j.sal.fs.joinPaths(self.BUILDDIRL, 'usr/sbin')):
            self.cuisine.core.file_copy(item, bindir + '/')

    def start(self):
        self.cuisine.bash.profileDefault.addPath(self.cuisine.core.replace("$BINDIR"))
        self.cuisine.bash.profileDefault.save()
        self.cuisine.processmanager.ensure('zerotier-one', 'zerotier-one')

    def stop(self):
        self.cuisine.processmanager.stop('zerotier-one')

    def join_network(self, network_id):
        """
        join the netowrk identied by network_id
        """
        cmd = '{cli} join {id}'.format(cli=self.CLI, id=network_id)
        rc, out, err = self.cuisine.core.run(cmd, die=False)
        if rc != 0 or out.find('OK') == -1:
            raise j.exceptions.RuntimeError("error while joinning network: \n{}".format(err))

    def leave_network(self, network_id):
        """
        leave the netowrk identied by network_id
        """
        cmd = '{cli} leave {id}'.format(cli=self.CLI, id=network_id)
        rc, out, _ = self.cuisine.core.run(cmd, die=False)
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
        rc, out, _ = self.cuisine.core.run(cmd, die=False)
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
        rc, out, _ = self.cuisine.core.run(cmd, die=False)
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
