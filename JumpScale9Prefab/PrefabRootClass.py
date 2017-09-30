
from js9 import j


# from JumpScale9Prefab.PrefabPackage import PrefabPackage
# from JumpScale9Prefab.PrefabProcess import PrefabProcess
# from JumpScale9Prefab.PrefabNet import PrefabNet
# from JumpScale9Prefab.PrefabSSH import PrefabSSH
# from JumpScale9Prefab.PrefabNS import PrefabNS
# from JumpScale9Prefab.PrefabUser import PrefabUser
# # from JumpScale9Prefab.PrefabBuilder import PrefabBuilder
# from JumpScale9Prefab.PrefabGroup import PrefabGroup
# from JumpScale9Prefab.ProcessManagerFactory import ProcessManagerFactory
# from JumpScale9Prefab.PrefabTmux import PrefabTmux
from JumpScale9Prefab.PrefabCore import PrefabCore
# from JumpScale9Prefab.PrefabPNode import PrefabPNode

# from JumpScale9Prefab.apps.apps import apps
# from JumpScale9Prefab.development.development import development
# from JumpScale9Prefab.examples.examples import examples
# from JumpScale9Prefab.solutions.solutions import solutions
# from JumpScale9Prefab.systemservices.systemservices import systemservices
# from JumpScale9Prefab.testscripts.testscripts import testscripts
# from JumpScale9Prefab.tools.tools import tools


class PrefabRootClass:

    def __init__(self, executor):
        self.executor=executor

        self._platformtype = None
        self._id = None
        # self._package = None
        # self._processmanager = None
        # self._process = None
        # self._ns = None
        # self._ssh = None
        # self._net = None
        # self._group = None
        # self._user = None
        self._bash = None
        # self._tmux = None
        # self.prefab = self
        # self._fqn = ""
        # self._builder = None

        # self._apps = None
        # self._development = None
        # self._examples = None
        # self._solutions = None
        # self._systemservices = None
        # self._testscripts = None
        # self._tools = None

        self.core = PrefabCore(self.executor, self)
        # self.pnode = PrefabPNode(self.executor, self)

        # self.reset = self.core.reset

    # @property
    # def apps(self):
    #     if self._apps is None:
    #         self._apps = apps(self.executor, self)
    #     return self._apps

    # @property
    # def development(self):
    #     if self._development is None:
    #         self._development = development(self.executor, self)
    #     return self._development

    # @property
    # def examples(self):
    #     if self._examples is None:
    #         self._examples = examples(self.executor, self)
    #     return self._examples

    # @property
    # def solutions(self):
    #     if self._solutions is None:
    #         self._solutions = solutions(self.executor, self)
    #     return self._solutions

    # @property
    # def systemservices(self):
    #     if self._systemservices is None:
    #         self._systemservices = systemservices(self.executor, self)
    #     return self._systemservices

    # @property
    # def testscripts(self):
    #     if self._testscripts is None:
    #         self._testscripts = testscripts(self.executor, self)
    #     return self._testscripts

    # @property
    # def tools(self):
    #     if self._tools is None:
    #         self._tools = tools(self.executor, self)
    #     return self._tools

    # @property
    # def btrfs(self):
    #     return j.sal.btrfs.getBtrfs(self.executor)

    # @property
    # def package(self):
    #     if self._package is None:
    #         self._package = PrefabPackage(self.executor, self)
    #     return self._package

    # @property
    # def process(self):
    #     if self._process is None:
    #         self._process = PrefabProcess(self.executor, self)
    #     return self._process

    # @property
    # def tmux(self):
    #     if self._tmux is None:
    #         self._tmux = PrefabTmux(self.executor, self)
    #     return self._tmux

    # # @property
    # # def builder(self):
    # #     if self._builder is None:
    # #         self._builder = PrefabBuilder(self.executor, self)
    # #     return self._builder

    @property
    def id(self):
        return self.executor.id

    @property
    def platformtype(self):
        if self._platformtype is None:
            self._platformtype = j.core.platformtype.get(self.executor)
        return self._platformtype

    # @property
    # def ns(self):
    #     if self._ns is None:
    #         self._ns = PrefabNS(self.executor, self)
    #     return self._ns

    # @property
    # def ssh(self):
    #     if self._ssh is None:
    #         self._ssh = PrefabSSH(self.executor, self)
    #     return self._ssh

    @property
    def bash(self):
        if self._bash is None:
            self._bash = j.tools.bash.get(executor=self.executor)
        return self._bash

    # @property
    # def net(self):
    #     if self._net is None:
    #         self._net = PrefabNet(self.executor, self)
    #     return self._net

    # @property
    # def user(self):
    #     if self._user is None:
    #         self._user = PrefabUser(self.executor, self)
    #     return self._user

    # @property
    # def group(self):
    #     if self._group is None:
    #         self._group = PrefabGroup(self.executor, self)
    #     return self._group

    # @property
    # def processmanager(self):
    #     if self._processmanager is None:
    #         self._processmanager = ProcessManagerFactory(self).get()
    #     return self._processmanager

    def __str__(self):
        return "prefabcat:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))

    __repr__ = __str__
