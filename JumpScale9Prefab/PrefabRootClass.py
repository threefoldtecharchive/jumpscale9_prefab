
from js9 import j

from JumpScale9Prefab.PrefabCore import PrefabCore


class PrefabRootClass:

    def __init__(self, executor):
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
        if self.executor.type == "local":
            return "prefab:local"
        else:
            return "prefab:%s:%s" % (getattr(self.executor.sshclient, 'addr', 'local'), getattr(self.executor.sshclient, 'port', ''))

    __repr__ = __str__
