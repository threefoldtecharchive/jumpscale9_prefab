
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

        am sure other params are required

        this installer will
        - use first node as master
        - deploy/generate required secrets/keys to allow user to access this kubernetes
        - make sure that dashboard is installed as well on kubernetes
        - use /storage inside the node (make sure is btrfs partition?) as the backend for kubernetes
        - deploy zerotier network (optional) into the node which connects to the kubernetes (as pub network?)

        """
        pass

    def build(self, reset=False):

        if self.doneCheck("build", reset):
            return

        # TODO

        self.doneSet("build")
