from Jumpscale import j
import json
base = j.tools.prefab._getBaseClass()


class PrefabZerotier(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("{DIR_VAR}/build/zerotier/")
        if "LEDE" in self.prefab.platformtype.osname:
            self.CLI = 'zerotier-cli'
        else:
            self.CLI = j.sal.fs.joinPaths('{DIR_BIN}', 'zerotier-cli')


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
            self.prefab.core.run("opkg update")
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
        if self.prefab.core.isMac:
            cmd = "cd {code} && make install-mac-tap".format(code=codedir, build=self.BUILDDIRL)
            bindir = '{DIR_BIN}'
            self.prefab.core.dir_ensure(bindir)
            for item in ['zerotier-cli', 'zerotier-idtool', 'zerotier-one']:
                self.prefab.core.file_copy('{code}/{item}'.format(code=codedir, item=item), bindir+'/')
            return
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
        bindir = '{DIR_BIN}'
        self.prefab.core.dir_ensure(bindir)

        if self.prefab.core.isMac:
            return

        for item in self.prefab.core.find(j.sal.fs.joinPaths(self.BUILDDIRL, 'usr/sbin')):
            self.prefab.core.file_copy(item, bindir + '/')

    def start(self):
        self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("{DIR_BIN}"))
        self.prefab.bash.profileDefault.save()
        pm = self.prefab.system.processmanager.get()
        pm.ensure('zerotier-one', cmd='zerotier-one')

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop('zerotier-one')

    def network_join(self, network_id, config_path=None, zerotier_client=None):
        """
        join the netowrk identied by network_id and authorize it into the network if a zerotier_client would be given
        """
        switches = self._get_switches(config_path)
        cmd = '{cli} {switches}join {id}'.format(cli=self.CLI, switches=switches, id=network_id)
        rc, out, err = self.prefab.core.run(cmd, die=False)
        if rc != 0 or out.find('OK') == -1:
            raise j.exceptions.RuntimeError("error while joinning network: \n{}".format(err))
        if zerotier_client:
            machine_address = self.get_zerotier_machine_address()
            zerotier_client.client.network.updateMember(address=machine_address, id=network_id,
                                                    data={"config": {"authorized": True}})

    def network_leave(self, network_id, config_path=None):
        """
        leave the netowrk identied by network_id
        """
        switches = self._get_switches(config_path)
        cmd = '{cli} {switches}leave {id}'.format(cli=self.CLI, switches=switches, id=network_id)
        rc, out, _ = self.prefab.core.run(cmd, die=False)
        if rc != 0 or out.find('OK') == -1:
            error_msg = "error while joinning network: "
            if out.find("404") != -1:
                error_msg += 'not part of the network {}'.format(network_id)
            else:
                error_msg += out
            raise j.exceptions.RuntimeError(error_msg)

    def networks_list(self, config_path=None):
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
        switches = self._get_switches(config_path)
        cmd = '{cli} -j {switches}listnetworks'.format(cli=self.CLI, switches=switches)
        rc, out, _ = self.prefab.core.run(cmd, die=False)
        if rc != 0:
            raise j.exceptions.RuntimeError(out)
        lines = json.loads(out)
        if len(lines) < 1:
            return {}

        networks = []
        for line in lines:
            network = {
                'network_id': line['id'],
                'name': line['name'],
                'mac': line['mac'],
                'status': line['status'],
                'type': line['type'],
                'dev': line['portDeviceName'],    
                'ips': line['assignedAddresses'],
            }
            networks.append(network)

        return networks

    def get_network_interface_name(self, network_id, config_path=None):
        """
        Get the zerotier network interface device name.
        """
        for net in self.networks_list(config_path=config_path):
            if net['network_id'] == network_id:
                return net['dev']
        raise KeyError("Network connection with id %s was not found!" % network_id)
    
    def get_zerotier_machine_address(self, config_path=None):
        """
        Get the zerotier machine address.
        """
        switches = self._get_switches(config_path)
        cmd = '{cli} {switches}info'.format(cli=self.CLI, switches=switches)
        _, out, _ = self.prefab.core.run(cmd)
        return out.split()[2]

    def peers_list(self, config_path=None):
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
        switches = self._get_switches(config_path)
        cmd = '{cli} {switches}listpeers'.format(cli=self.CLI, switches=switches)
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


    def network_name_get(self, network_id, config_path=None):
        """"gets a network name with ip
        
        Arguments:
            network_id {string} -- network id to look for
        
        Raises:
            RuntimeError -- if there is no networks with the given id
        
        Returns:
            string -- network name
        """

        networks = self.networks_list(config_path=config_path)
        for network in networks:
            if network['network_id'] == network_id:
                return network['name']
        raise RuntimeError("no networks found with id {}, make sure that you properly joined this network".format(network_id))
    
    def _get_switches(self, config_path=None):
        switches = ''
        if config_path:
            switches += "-D%s " % config_path
        return switches
