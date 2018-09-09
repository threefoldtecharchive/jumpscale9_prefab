from Jumpscale import j


class Machines:
    """This class give you access to machine related actions from the kvm sal over prefab"""

    def __init__(self, controller):
        self._controller = controller

    def create(self, name, os='xenial-server-cloudimg-amd64-uefi1.img',
               disks=[10], storage_pool='vms',
               nics=['vms1'], memory=512, cpucount=1,
               cloud_init=True, username="root", passwd="gig1234", sshkey=None, resetPassword=True,
               start=True):
        """
        @param name str: machine name.
        @param os str: os name to use.
        @param disks list of int: size of disk names to be used by the machine.
                                  first of the list is the size of the boot disk, remaining are data disks
        @param storage_pool str: name of the storage to use when creating disks
        @param nics [str]: name of networks to be used with machine. need to be created before. (prefab.systemservices.kvm.networks.create())
        @param memory int: disk memory in Mb.
        @param cpucount int: number of cpus to use.
        @param cloud_init bool: option to use cloud_init passing creating and passing ssh_keys, user name and passwd to the image
        @param username string: if cloud_init is used, username to set password to
        @param passwd string: password of the username to set
        @param sshkey string: public sshkey to authorize into the vm
        @param resetPassword bool: generate random password
        @param start bool: start the machine after creation

        @param pubkey is the key which will be used to get access to this kvm, if none then use the std ssh key as used for docker
        """
        machine = j.sal.kvm.CloudMachine(self._controller, name, os, disks,
                                         nics, memory, cpucount, poolname=storage_pool, cloud_init=cloud_init)

        machine.create(username=username, passwd=passwd, sshkey=sshkey)

        if start:
            machine.start()
            if resetPassword:
                machine.prefab.core.sudo("echo '%s:%s' | chpasswd" % (
                    getattr(machine.executor, 'login', 'root'),
                    j.data.idgenerator.generatePasswd(10).replace("'", "'\"'\"'")))

        return machine

    def list(self):
        """
        list all vms
        """
        return self._controller.list_machines()

    def get_by_name(self, name):
        """
        return a machine object if the vm with that name exists

        @param name str: name of the vm
        """
        return j.sal.kvm.Machine.get_by_name(self._controller, name)

    def get_path(self, name):
        """
        returns the path of the boot disk of the vm with name `name`

        @param name str: name of the vm
        """
        return j.sal.fs.joinPaths(self._controller.base_path, "vms", name)
