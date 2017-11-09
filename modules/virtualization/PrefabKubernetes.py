
from js9 import j
import random
import time

app = j.tools.prefab._getBaseAppClass()


class PrefabKubernetes(app):
    NAME = "kubectl"

    def minikube_install(self, reset=False):
        """
        install full minikube, only support ubuntu 16.04+ (check this)
        """

        if self.doneCheck("minikube_install", reset):
            return

        self.install_dependencies()

        self.doneSet("minikube_install")

    def multihost_install(self, nodes=[], reset=False):
        """

        @param nodes are list of prefab clients which will be used to deploy kubernetes


        this installer will
        - use first node as master
        - deploy/generate required secrets/keys to allow user to access this kubernetes
        - make sure that dashboard is installed as well on kubernetes
        - use /storage inside the node (make sure is btrfs partition?) as the backend for kubernetes
        - deploy zerotier network (optional) into the node which connects to the kubernetes (as pub network?)

        """
        pass

    def install_dependencies(self, reset=False):
        """
        Use the go get command to get dependencies and install.

        @param reset ,,if True will resintall even if the code has been run before.
        """
        if self.doneCheck("install_dependencies", reset):
            return

        # install requirement for the running kubernetes basics
        self.prefab.system.package.install('mercurial')
        self.prefab.system.package.install('conntrack')
        self.prefab.runtimes.golang.install()
        self.prefab.virtualization.docker.install(branch='1.13')

        # required for bridge manipulation in ubuntu
        if self.prefab.local.core.isUbuntu:
            self.prefab.system.package.install('bridge-utils')

        self.doneSet("install_dependencies")

    def install(self, reset=False):
        """
        Builds the kubernetes binaries and Moves them to the appropriate location

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        """
        if self.doneCheck("install", reset):
            return

        self.install_dependencies()
        path = '%s/kubernetes' % j.dirs.TMPDIR

        # get and expand tar
        self.prefab.core.file_download(
            'https://github.com/kubernetes/kubernetes/releases/download/v1.7.10/kubernetes.tar.gz', to=j.dirs.TMPDIR)
        self.prefab.core.file_expand(
            '%s/kubernetes.tar.gz' % j.dirs.TMPDIR, j.dirs.TMPDIR)

        # get binaries
        self.prefab.core.run(
            'cd %s/clusters && bash get-kube-binaries.sh' % path)
        self.prefab.core.run(
            'cd %s/server && tar xf kubernetes-server*' % path)
        self.prefab.core.run('cp %s/server/kubernetes/server/bin/!(*.*) %s' % (path, j.dirs.BINDIR))


        # build  kube-apiserver, kube-controller-manager, kube-scheduler docker images
        kube_binary_path = '%s/server/kubernetes/server/bin' % path
        for image_path in j.tools.prefab.local.core.find(kube_binary_path, False, pattern='*.tar'):
            self.prefab.core.run('docker load -i %s' % image_path)


        # build etcd image
        self.prefab.core.run('cd %s/cluster/images/etcd && make' % path)
        self.prefab.bash.envSet('TAG', '1.7.10')
        self.prefab.bash.envSet(
            'ETCD_IMAGE', 'gcr.io/google_containers/etcd-amd64')

        # build
        self.doneSet("install")


    def configure_networking(self, reset, working_ip=None, kube_cidr='10.0.0.0/16'):
        if self.doneCheck("configure_netwokring", reset):
            return

        if not self.prefab.core.isUbuntu:
            raise RuntimeError('Only ubuntu system networking is supported at the moment, manual setup will still work')

        # clean up docker bridge
        self.prefab.core.run('docker network rm bridge')
        docker_deamon_config = j.data.serializer.json.dumps({'bridge': 'cbr0', 'iptables': False, 'ip-masq': False })
        self.prefab.core.file_write('/etc/docker/daemon.json', docker_deamon_config)

        # find physical interface or specified interface make a slave of the new bridge allow bridge to take aquire ip
        # set up new bridge to route traffic through and connect to docker deamon
        used_interface_name = None
        for device in self.prefab.core.getNetworkInfoGenrator():
            if working_ip:
                if device['ip'] == working_ip:
                    used_interface_name = device['name']
                    break

            if not getattr(self.prefab.executor, 'addr', None):
                raise RuntimeError('No connected ip specified , please provide internet connected ip.')
            if device['ip'] == getattr(self.prefab.executor, 'addr', ''):
                used_interface_name = device['name']
                break

        _interfaces_script = """
        auto lo
        iface lo inet loopback

        auto {interface}
        #iface ens3 inet manual

        auto cbr0
        iface cbr0 inet dhcp
        bridge_ports {interface}
        """.format(interface=used_interface_name)
        self.prefab.core.file_write('/etc/network/interfaces.d/kube.cfg', _interfaces_script)
        self.prefab.core.run('service networking restart')
        timer = time.time()+20
        while time.time() < timer:
            if self.prefab.executor.test():
                break
        else:
            raise RuntimeError("Something went wrong in the network configuration check 'journalctl -u networking' ")

        self.prefab.core.run('service stop docker')
        self.prefab.bash.envSet('SERVICE_CLUSTER_IP_RANGE', kube_cidr)


#     def define_configuration(self, apiversion='v1', clusters=None, contexts=None, users=None):
#         """
#         Creates the configuration file for kubernetes
#         @param clusters,,list(dict) define cluster configs,

#         example :
#         [
#             {"cluster": {
#                         "certificate-authority": "/etc/kubernetes/ca.pem",
#                         "server": "https://node0.c.kubestack.internal:6443"
#                         },
#             "name": "kubernetes"
#             }
#         ]

#         @param contexts,,list(dict) define context configs,

#         example :
#         [
#         { "context": { "cluster": "kubernetes", "user": "kubelet"},
#           "name": "kubelet-to-kubernetes" }
#         ]

#         @param users,, list(dict) define  users configs,

#         example :
#         [
#         {
#             "name": "kubelet",
#             "user": {
#                 "client-certificate": "/etc/kubernetes/client.pem",
#                 "client-key": "/etc/kubernetes/client-key.pem"
#             }
#         }
#         ]
#         TODO

#         """
# #         delete_docker_net_cmd = """
# # iptables -t nat -F
# # ip link set docker0 down
# # ip link delete docker0
# #         """
# #         self.prefab.core.execute_bash(delete_docker_net_cmd, profile=True)
#         if users:
#             pass
#         if clusters:
#             pass
#         if contexts:
#             pass

#         config={
#             'apiversion': apiversion,
#             'clusters': clusters,
#             'users': users
#         }

    def start_node(self, reset=True, auth_path=None, labels={}):
        """
        Registers the current prefab connection as a new node to the defined master

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        @param auth_path,,str  Path to credentials to authenticate itself to the apiserver.
        @param  labels,, dict(str, str) Labels to add when registering the node in the cluster.
        TODO
        """
        if self.doneCheck("install", reset):
            return

        pm=self.prefab.system.processmanager.get()
        if auth_path:
            pass
        if labels:
            pass

        cmd='kubelet '
        pm.enusre(name='kubelet',)

        self.doneSet("install")

    def start_master(self, reset, auth_path, labels={}):
        pass
