from Jumpscale import j

base = j.tools.prefab._BaseClass

# from JumpscaleLib.sal.disklayout.DiskManager import DiskManager
raise NotImplemented()


class PrefabDiskManager(base,DiskManager):

    def __init__(self,executor, prefab):
        DiskManager.__init__(self)
        base.__init__(self, executor, prefab)

    def _init(self):
        self.set_executor(self.executor)
        self.getDisks()
