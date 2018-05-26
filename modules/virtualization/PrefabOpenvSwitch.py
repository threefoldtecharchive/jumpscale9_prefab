
from js9 import j

app = j.tools.prefab._getBaseAppClass()

# TODO: *3 see if this works on packet, net

# make sure you use the trick we used in jumpscale/core9/lib/JumpScale/tools/prefab/systemservices/PrefabFW.py
#   : setRuleset...   here we use a python script to make sure we set & set back to original if it doesn't work

# can we use j.sal.openvswitch & i saw there is already an .executor in,
# is it usable everywhere?

# please spec properly


class PrefabOpenvSwitch(app):
    """
    usage:

    ```
    c=j.tools.prefab.get("ovh4")
    c.virtualization.openvswitch.install()
    ```

    """

    def _init(self):
        self.__controller = None
        self._apt_packages = ['openssl', 'openvswitch-switch', 'openvswitch-common']

    @property
    def _controller(self):
        if not self.__controller:
            self.__controller = j.sal.kvm.KVMController(
                executor=self.prefab.executor)
        return self.__controller

    # def prepare(self):

    #     self.install()

    #     # check openvswitch properly configured

    def isInstalled(self):
        try:
            self.prefab.core.run("ovs-vsctl show")
            return True
        except Exception as e:
            return False

    def install(self):
        if self.isInstalled():
            return
        if self.prefab.core.isUbuntu:
            self.prefab.system.package.install(self._apt_packages)
        else:
            raise RuntimeError("only support ubuntu")
        # do checks if openvswitch installed & configured properly if not
        # install

    def uninstall(self):
        if not self.isInstalled():
            return
        for package in self._apt_packages:
            self.prefab.core.package.remove(package)

    def networkCreate(self, network_name, bridge_name=None, interfaces=None, ovs=True, start=True):
        """
        Create a network interface using libvirt and open v switch.

        @network_name str: name of the network
        @bridge_name str: name of the main bridge created to connect to th host
        @interfaces [str]: names of the interfaces to be added to the bridge
        """
        raise RuntimeError("not implemented")
        network = j.sal.kvm.Network(
            self._controller, network_name, bridge_name, interfaces, ovs=ovs)
        network.create()
        if start:
            network.start()

    def networkDelete(self, bridge_name):
        """
        Delete network and bridge related to it.

        @bridge_name
        """
        raise RuntimeError("not implemented")
        network = j.sal.kvm.Network(self._controller, bridge_name)
        return network.destroy()

    def networkList(self):
        """
        List bridges available on machaine created by openvswitch.
        """
        _, out, _ = self.prefab.core.run("ovs-vsctl list-br")
        return out.splitlines()

    def networkListInterfaces(self, name):
        """
        List ports available on bridge specified.
        """
        _, out, _ = self.prefab.core.run("ovs-vsctl list-ports %s" % name)
        return out.splitlines()

    def vnicCreate(self, name, bridge):
        """
        Create and interface and relevant ports connected to certain bridge or network.

        @name  str: name of the interface and port that will be creates
        @bridge str: name of bridge to add the interface to
        @qos int: limit the allowed rate to be used by interface
        """
        # is a name relevant???, how do we identify a vnic
        raise RuntimeError("not implemented")
        interface = j.sal.kvm.Interface(self._controller, name, bridge)
        self.interfaces[name] = interface
        interface.create()

    def vnicDelete(self, name, bridge):
        """
        Delete interface and port related to certain machine.

        @bridge str: name of bridge
        @name str: name of port and interface to be deleted
        """
        raise RuntimeError("not implemented")
        interface = j.sal.kvm.Interface(self._controller, name, bridge)
        return interface.destroy()

    def vnicQOS(self, name, bridge, qos, burst=None):
        """
        Limit the throughtput into an interface as a for of qos.

        @interface str: name of interface to limit rate on
        @qos int: rate to be limited to in Kb
        @burst int: maximum allowed burst that can be reached in Kb/s
        """
        # goal is we can do this at runtime
        raise RuntimeError("not implemented")
        interface = j.sal.kvm.Interface(self._controller, name, bridge)
        interface.qos(qos, burst)

    def vnicBond(self, parameter_list):
        raise NotImplemented("in development")
