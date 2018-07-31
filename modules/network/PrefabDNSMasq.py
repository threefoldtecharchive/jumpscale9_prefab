from jumpscale import j

base = j.tools.prefab._getBaseClass()

from JumpscaleLib.sal.dnsmasq.Dnsmasq import DNSMasq


class PrefabDNSMasq(base,DNSMasq):

    def __init__(self,executor, prefab):
        base.__init__(self, executor, prefab)

