
from Jumpscale import j

from JumpscalePrefab.PrefabCore import PrefabCore

JSBASE = j.application.JSBaseClass


class PrefabRootClass(JSBASE):
    """
    there is one instance created per executor
    this is the root of the prefab
    """

    def __init__(self, executor):
        JSBASE.__init__(self)
        self.executor = executor

        self._platformtype = None
        self._id = None
        self._bash = None
        self.core = PrefabCore(self.executor, self)

    @property
    def id(self):
        return self.executor.id

    @property
    def platformtype(self):
        if self._platformtype is None:
            self._platformtype = j.core.platformtype.get(self.executor)
        return self._platformtype

    @property
    def bash(self):
        if self._bash is None:
            self._bash = j.tools.bash.get(executor=self.executor)
        return self._bash

    def __str__(self):
        return "prefab_rootobj:%s" % repr(self.executor)

    __repr__ = __str__
