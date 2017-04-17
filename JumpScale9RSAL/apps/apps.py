from JumpScale import j

base = j.tools.cuisine._getBaseClassLoader()


class apps(base):

    def __init__(self, executor, cuisine):
        self._dnsmasq = None
        base.__init__(self, executor, cuisine)

    @property
    def dnsmasq(self):
        if self._dnsmasq is None:
            self._dnsmasq = j.sal.dnsmasq
            self._dnsmasq.cuisine = self.cuisine
            self._dnsmasq.executor = self.executor
        return self._dnsmasq
