from Jumpscale import j

base = j.tools.prefab._BaseClass

from JumpscaleLib.sal.dnsmasq.Dnsmasq import DNSMasq


class PrefabDNSMasq(base,DNSMasq):

    def __init__(self,executor, prefab):
        base.__init__(self, executor, prefab)

