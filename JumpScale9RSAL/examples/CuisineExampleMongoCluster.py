
from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineExampleMongoCluster(base):

    def install(self, pubkey=None):
        c = self.cuisine

        if not c.core.isUbuntu or c.platformtype.osversion != '16.04':
            raise RuntimeError("only support ubuntu 16.04")

        # install kvm
        c.systemservices.kvm.install()

        # install OpenVswitch
        c.systemservices.openvswitch.install()

        c.processmanager.start('libvirt-bin')

        # create bridge vms1
        c.systemservices.openvswitch.networkCreate("vms1")
        # configure the network and the natting
        c.net.netconfig('vms1', '10.0.4.1', 24, masquerading=True, dhcp=True)
        c.processmanager.start('systemd-networkd')
        # add a dhcp sercer to the bridge
        c.apps.dnsmasq.install()
        c.apps.dnsmasq.config('vms1')

        # create a pool for the images and virtual disks
        c.systemservices.kvm.storage_pools.create("vms")

        # get xenial server cloud image
        c.systemservices.kvm.disks.download_image(
            "https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-uefi1.img")

        # create a virutal machine kvm1 with the default settings
        kvm1 = c.systemservices.kvm.machines.create("kvm1")
        # create a virutal machine kvm2 with the default settings
        kvm2 = c.systemservices.kvm.machines.create("kvm2")

        # enable sudo mode
        kvm1.cuisine.core.sudomode = True
        kvm2.cuisine.core.sudomode = True

        kvm1.cuisine.development.js8.install()
        kvm2.cuisine.development.js8.install()

        # TODO docker is preconfigured & jumpscale inside with our G8OS fuse
        # layer (to keep image small), host this image & use as standard
        # when creating KVM this image is autobuilded using our docker
        # build system !!!

        # create docker containers
        nodes = []
        for i in range(5):
            nodes.append(kvm1.cuisine.systemservices.docker.dockerStart(
                "n%s" % i, ports='', pubkey=pubkey, weave=True, ssh=False).executor)
        for i in range(5, 10):
            nodes.append(kvm2.cuisine.systemservices.docker.dockerStart(
                "n%s" % i, ports='', pubkey=pubkey, weave=True, ssh=False, weavePeer=kvm1.ip).executor)

        # create mongo cluster on the docker containers
        self.solutions.mongocluster.createCluster(nodes)
