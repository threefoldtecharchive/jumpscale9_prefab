from js9 import j

base = j.tools.cuisine._getBaseClassLoader()

from JumpScale.sal.disklayout.DiskManager import DiskManager


class tools(base):

    def __init__(self, executor, cuisine):
        base.__init__(self, executor, cuisine)

    @property
    def diskmanager(self):
        dm = DiskManager()
        dm.set_executor(self.executor)
        dm.getDisks()
        return dm
