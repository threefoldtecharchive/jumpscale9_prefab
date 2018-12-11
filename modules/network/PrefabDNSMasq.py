from JumpscaleLib.sal.dnsmasq.Dnsmasq import DNSMasq
from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabDNSMasq(base, DNSMasq):

    def __init__(self, executor, prefab):
        base.__init__(self, executor, prefab)
