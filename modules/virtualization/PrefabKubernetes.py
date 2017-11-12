
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
        self.prefab.system.package.install('mercurial,conntrack,ntp')
        self.prefab.runtimes.golang.install()
        self.prefab.virtualization.docker.install(branch='1.12')

        # required for bridge manipulation in ubuntu
        if self.prefab.core.isUbuntu:
            self.prefab.system.package.install('bridge-utils')

        self.doneSet("install_dependencies")

    def install_base(self, reset=False):
        """
        Builds the kubernetes binaries and Moves them to the appropriate location

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        """
        if self.doneCheck("install_base", reset):
            return

        if not self.prefab.core.isUbuntu:
            raise RuntimeError('Only ubuntu systems are supported at the moment.')

        self.install_dependencies()
        script_content = """
        apt-get update && apt-get install -y apt-transport-https
        curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
        cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
        deb http://apt.kubernetes.io/ kubernetes-xenial main
        """
        self.prefab.core.run(script_content)
        self.prefab.system.package.mdupdate(reset=True)
        self.prefab.system.package.install('kubelet,kubeadm,kubectl')


        # build
        self.doneSet("install_base")


    def  install_master(self, reset=False, kube_cidr='10.0.0.0/16', flannel=True):
        if self.doneCheck("install_master", reset):
            return

        if flannel:
            kube_cidr = '10.244.0.0/16'

        self.install_base()

        rc, out, err = self.prefab.core.run('kubeadm init --pod-network-cidr=%s' % kube_cidr)
        if rc != 0:
            raise RuntimeError(err)
        for line in reversed(out.splitlines()):
            if line.startswith('  kubeadm join --token'):
                join_line = line
                break

        self.prefab.core.run(
            'kubectl --kubeconfig=/etc/kubernetes/admin.config apply -f https://raw.githubusercontent.com/coreos/flannel/v0.9.0/Documentation/kube-flannel.yml')

        log_message = """
        please wait until kube-dns deplyments are deployed before joining new nodes to the cluster.
        to check use this use 'kubectl get pods --all-namepspaces'
        then pass the join line returned string to the install_minion
        """
        print(log_message)

        return join_line


        # build
        self.doneSet("install_master")


    def  install_minion(self, join_line, reset=False):
        if self.doneCheck("install_minion", reset):
            return

        self.install_base()
        self.prefab.core.run(join_line.strip())

        # build
        self.doneSet("install_minion")
