from js9 import j

base = j.tools.prefab._getBaseClassLoader()

from JumpScale9Lib.sal.disklayout.DiskManager import DiskManager


class tools(base):

    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)

    @property
    def diskmanager(self):
        dm = DiskManager()
        dm.set_executor(self.executor)
        dm.getDisks()
        return dm
