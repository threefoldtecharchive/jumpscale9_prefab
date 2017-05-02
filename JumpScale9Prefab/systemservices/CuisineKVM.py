
from js9 import j
from JumpScale.tools.prefab.systemservices.kvm.Machines import Machines
from JumpScale.tools.prefab.systemservices.kvm.Disks import Disks
from JumpScale.tools.prefab.systemservices.kvm.StoragePools import StoragePools

base = j.tools.prefab._getBaseClass()


class CuisineKVM(base):
    """
    usage:

    ```
    c=j.tools.prefab.get("ovh4")
    c.systemservices.kvm.install()
    ```

    """

    def _init(self):
        self.__controller = None
        self._apt_packages = ['libvirt-bin', 'libvirt-dev', 'qemu-system-x86', 'qemu-system-common', 'genisoimage']
        self._pip_packages = ['libvirt-python==1.3.2']
        # submodules
        self._machines = None
        self._storage_pools = None
        self._disks = None
        self._networks = None

    @property
    def _controller(self):
        if not self.__controller:
            self.__controller = j.sal.kvm.KVMController(executor=self.prefab.executor)
        return self.__controller

    @property
    def path(self):
        return self._controller.base_path

    def install(self):
        """
        Install the dependencies required to run kvm (kvm, qemy, libvirt)
        """
        if not self.prefab.core.isUbuntu or self.prefab.platformtype.osversion != '16.04':
            raise RuntimeError("only support ubuntu 16.04")
        self.prefab.package.mdupdate()
        self.prefab.development.pip.ensure()
        self._libvirt()

    def _libvirt(self):
        """
        Install required packages for kvm
        """
        self.prefab.package.multiInstall(self._apt_packages)
        self.prefab.development.pip.multiInstall(self._pip_packages, upgrade=False)

    def uninstall(self):
        for package in self._apt_packages:
            self.prefab.package.remove(package)
        for package in self._pip_packages:
            self.prefab.development.pip.packageRemove(package)

    """
    Sub modules of the prefab KVM
    """

    @property
    def machines(self):
        if self._machines is None:
            self._machines = Machines(self._controller)
        return self._machines

    @property
    def storage_pools(self):
        if self._storage_pools is None:
            self._storage_pools = StoragePools(self._controller)
        return self._storage_pools

    @property
    def disks(self):
        if self._disks is None:
            self._disks = Disks(self._controller)
        return self._disks

    @property
    def networks(self):
        raise NotImplementedError("Not implemented yet. use 'prefab.systemservices.openvswitch' for now")
        # if self._networks is None:
        #     self._networks = Machines(self._controller)
        # return self._networks
