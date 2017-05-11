from js9 import j

base = j.tools.prefab._getBaseClassLoader()


class apps(base):

    def __init__(self, executor, prefab):
        self._dnsmasq = None
        base.__init__(self, executor, prefab)
        self.prefab.core.dir_paths_create()

    @property
    def dnsmasq(self):
        if self._dnsmasq is None:
            self._dnsmasq = j.sal.dnsmasq
            self._dnsmasq.prefab = self.prefab
            self._dnsmasq.executor = self.executor
        return self._dnsmasq
