
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

        self.prefab.system.package.install('mercurial')
        self.prefab.system.package.install('conntrack')
        golang = self.prefab.runtimes.golang
        golang.install()
        self.prefab.virtualization.docker.install()
        golang.get('k8s.io/kubernetes/...', install=False, update=False)
        self.prefab.core('cd %s/src/k8s.io/kubernetes && bash hack/install-etcd.sh' %
                         self.prefab.runtimes.golang.GOPATH)

        self.doneSet("install_dependencies")

    def build(self, reset=False):
        """
        Build the kubernetes binaries for both master in node.

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        """
        if self.doneCheck("build", reset):
            return

        self.install_dependencies(reset)
        self.prefab.core.run(
            'cd %s/src/k8s.io/kubernetes && make kubectl kube ' % self.prefab.runtimes.golang.GOPATH)

        self.doneSet("build")

    def install(self, reset=False):
        """
        Builds the kubernetes binaries and Moves them to the appropriate location

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        """
        if self.doneCheck("install", reset):
            return

        self.build(reset)
        for file in self.prefab.core.find('%s/src/k8s.io/kubernetes/_output/' % self.prefab.runtimes.golang.GOPATH,
                                          pattern='kube*', type='f'):
            self.prefab.core.file_copy(file, '$BINDIR/')

        self.doneSet("install")

    def define_configuration(self, apiversion='v1', clusters=None, contexts=None, users=None):
        """
        Creates the configuration file for kubernetes
        @param clusters,,list(dict) define cluster configs,

        example :
        [
            {"cluster": {
                        "certificate-authority": "/etc/kubernetes/ca.pem",
                        "server": "https://node0.c.kubestack.internal:6443"
                        },
            "name": "kubernetes"
            }
        ]

        @param contexts,,list(dict) define context configs,

        example :
        [
        { "context": { "cluster": "kubernetes", "user": "kubelet"},
          "name": "kubelet-to-kubernetes" }
        ]

        @param users,, list(dict) define  users configs,

        example :
        [
        {
            "name": "kubelet",
            "user": {
                "client-certificate": "/etc/kubernetes/client.pem",
                "client-key": "/etc/kubernetes/client-key.pem"
            }
        }
        ]
        TODO

        """
#         delete_docker_net_cmd = """
# iptables -t nat -F
# ip link set docker0 down
# ip link delete docker0
#         """
#         self.prefab.core.execute_bash(delete_docker_net_cmd, profile=True)
        if users:
            pass
        if clusters:
            pass
        if contexts:
            pass

        config  =  {
            'apiversion': apiversion,
            'clusters': clusters,
            'users': users
        }





    def define_node(self, reset=True, auth_path=None, labels={}):
        """
        Registers the current prefab connection as a new node to the defined master

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        @param auth_path,,str  Path to credentials to authenticate itself to the apiserver.
        @param  labels,, dict(str, str) Labels to add when registering the node in the cluster.
        TODO
        """
        if self.doneCheck("install", reset):
            return

        pm = self.prefab.system.processmanager.get()
        if auth_path:
            pass
        if labels:
            pass

        cmd = 'kubelet '
        pm.enusre(name='kubelet',  )

        self.doneSet("install")

