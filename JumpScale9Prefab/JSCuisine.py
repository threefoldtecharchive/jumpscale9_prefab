
from js9 import j


from JumpScale.tools.prefab.CuisinePackage import CuisinePackage
from JumpScale.tools.prefab.CuisineProcess import CuisineProcess
from JumpScale.tools.prefab.CuisineNet import CuisineNet
from JumpScale.tools.prefab.CuisineSSH import CuisineSSH
from JumpScale.tools.prefab.CuisineNS import CuisineNS
from JumpScale.tools.prefab.CuisineUser import CuisineUser
# from JumpScale.tools.prefab.CuisineBuilder import CuisineBuilder
from JumpScale.tools.prefab.CuisineGroup import CuisineGroup
from JumpScale.tools.prefab.ProcessManagerFactory import ProcessManagerFactory
from JumpScale.tools.prefab.CuisineTmux import CuisineTmux
from JumpScale.tools.prefab.CuisineCore import CuisineCore
from JumpScale.tools.prefab.CuisinePNode import CuisinePNode

from JumpScale.tools.prefab.apps.apps import apps
from JumpScale.tools.prefab.development.development import development
from JumpScale.tools.prefab.examples.examples import examples
from JumpScale.tools.prefab.solutions.solutions import solutions
from JumpScale.tools.prefab.systemservices.systemservices import systemservices
from JumpScale.tools.prefab.testscripts.testscripts import testscripts
from JumpScale.tools.prefab.tools.tools import tools


class JSCuisine:

    def __init__(self, executor):

        self.executor = executor

        self._platformtype = None
        self._id = None
        self._package = None
        self._processmanager = None
        self._process = None
        self._ns = None
        self._ssh = None
        self._net = None
        self._group = None
        self._user = None
        self._bash = None
        self._tmux = None
        self.prefab = self
        self._fqn = ""
        # self._builder = None

        self._apps = None
        self._development = None
        self._examples = None
        self._solutions = None
        self._systemservices = None
        self._testscripts = None
        self._tools = None

        self.core = CuisineCore(self.executor, self)
        self.pnode = CuisinePNode(self.executor, self)

        # self.reset = self.core.reset

    @property
    def apps(self):
        if self._apps is None:
            self._apps = apps(self.executor, self)
        return self._apps

    @property
    def development(self):
        if self._development is None:
            self._development = development(self.executor, self)
        return self._development

    @property
    def examples(self):
        if self._examples is None:
            self._examples = examples(self.executor, self)
        return self._examples

    @property
    def solutions(self):
        if self._solutions is None:
            self._solutions = solutions(self.executor, self)
        return self._solutions

    @property
    def systemservices(self):
        if self._systemservices is None:
            self._systemservices = systemservices(self.executor, self)
        return self._systemservices

    @property
    def testscripts(self):
        if self._testscripts is None:
            self._testscripts = testscripts(self.executor, self)
        return self._testscripts

    @property
    def tools(self):
        if self._tools is None:
            self._tools = tools(self.executor, self)
        return self._tools

    @property
    def btrfs(self):
        return j.sal.btrfs.getBtrfs(self.executor)

    @property
    def package(self):
        if self._package is None:
            self._package = CuisinePackage(self.executor, self)
        return self._package

    @property
    def process(self):
        if self._process is None:
            self._process = CuisineProcess(self.executor, self)
        return self._process

    @property
    def tmux(self):
        if self._tmux is None:
            self._tmux = CuisineTmux(self.executor, self)
        return self._tmux

    # @property
    # def builder(self):
    #     if self._builder is None:
    #         self._builder = CuisineBuilder(self.executor, self)
    #     return self._builder

    @property
    def id(self):
        return self.executor.id

    @property
    def platformtype(self):
        if self._platformtype is None:
            self._platformtype = j.core.platformtype.get(self.executor)
        return self._platformtype

    @property
    def ns(self):
        if self._ns is None:
            self._ns = CuisineNS(self.executor, self)
        return self._ns

    @property
    def ssh(self):
        if self._ssh is None:
            self._ssh = CuisineSSH(self.executor, self)
        return self._ssh

    @property
    def bash(self):
        if self._bash is None:
            self._bash = j.tools.bash.get(executor=self.executor)
        return self._bash

    @property
    def net(self):
        if self._net is None:
            self._net = CuisineNet(self.executor, self)
        return self._net

    @property
    def user(self):
        if self._user is None:
            self._user = CuisineUser(self.executor, self)
        return self._user

    @property
    def group(self):
        if self._group is None:
            self._group = CuisineGroup(self.executor, self)
        return self._group

    @property
    def processmanager(self):
        if self._processmanager is None:
            self._processmanager = ProcessManagerFactory(self).get()
        return self._processmanager

    def __str__(self):
        return "prefab:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))

    __repr__ = __str__
