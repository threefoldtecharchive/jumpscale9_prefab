
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
        @param reset ,,if True will resintall even if the code has been run before.
        use the go get command to get dependencies and install
        """
        if self.doneCheck("install_dependencies", reset):
            return

        self.prefab.system.package.install('mercurial')
        golang = self.prefab.runtimes.golang
        golang.install()
        self.prefab.virtualization.docker.install()
        golang.get('k8s.io/kubernetes/...', install=False, update=False)
        self.prefab.core('cd %s/src/k8s.io/kubernetes && bash hack/install-etcd.sh' % self.prefab.runtimes.golang.GOPATH)

        self.doneSet("install_dependencies")

    def build(self, reset=False):

        if self.doneCheck("build", reset):
            return

        self.install_dependencies(reset)
        self.prefab.core.run('cd %s/src/k8s.io/kubernetes && make' % self.prefab.runtimes.golang.GOPATH)


        self.doneSet("build")

    def install(self, reset=False):
        if self.doneCheck("install", reset):
            return
        self.build(reset)
        self.doneSet("install")
