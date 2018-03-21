from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZeroBoot(base):
    def install(self, network_id, token, reset=False):
        if self.donecheck("install") or reset:
            return
        # update zerotier config
        self.prefab.network.zerotier.build(install=True)
        
        self.prefab.core.run("/etc/init.d/zerotier enable")
        self.prefab.core.run("/etc/init.d/zerotier start")
        self.prefab.core.run("uci set zerotier.sample_config=zerotier")
        self.prefab.core.run("uci set zerotier.sample_config.enabled='1'")
        self.prefab.core.run("uci set zerotier.sample_config.interface='wan'") # restart ZT when wan status changed
        self.prefab.core.run("uci set zerotier.sample_config.join='{}'".format(network_id)) # Join zerotier network
        self.prefab.core.run("uci set uci set zerotier.sample_config.secret='generate'") # Generate secret on the first start
        self.prefab.core.run("uci commet")
        self.prefab.core.run("zerotier-cli join {network_id} -T {token}".format(network_id, token))

        # update TFTP and DHCP
        self.prefab.core.run("uci set dhcp.@dnsmasq[0].enable_tftp='1'")
        self.prefab.core.run("uci set dhcp.@dnsmasq[0].tftp_root='/opt/storage/'")
        self.prefab.core.run("uci set dhcp.@dnsmasq[0].dhcp_boot='pxelinux.0'")
        self.prefab.core.run("uci commet")

        self.prefab.core.dir_ensure('/opt/storage')
        self.prefab.core.run("wget https://raw.githubusercontent.com/0-complexity/G8_testing/master/pxe.tar.gz -O /opt/storage/pxe.tar.gz")
        self.prefab.core.run("tar -xzf /opt/storage/pxe.tar.gz -C /opt/storage")
        self.prefab.core.run("cp -r /opt/storage/pxe/* /opt/storage")
        self.prefab.core.run("rm -rf /opt/storage/pxe")
        self.prefab.core.run('sed "s|a84ac5c10a670ca3|%s|g" /opt/storage/pxelinux.cfg/default' % network_id)

        #TODO: get the real interface name instead of zt0
        self.prefab.core.run("uci set network.zt0=interface # Consider the zerotier network interface name is zt0")
        self.prefab.core.run("uci set network.zt0.proto='none'")
        self.prefab.core.run("uci set network.zt0.ifname='zt0'")
        self.prefab.core.run("uci set firewall.@zone[2]=zone")
        self.prefab.core.run("uci set firewall.@zone[2].input='ACCEPT'")
        self.prefab.core.run("uci set firewall.@zone[2].output='ACCEPT'")
        self.prefab.core.run("uci set firewall.@zone[2].name='zerotier'")
        self.prefab.core.run("uci set firewall.@zone[2].forward='ACCEPT'")
        self.prefab.core.run("uci set firewall.@zone[2].masq='1'")
        self.prefab.core.run("uci set firewall.@zone[2].network='zt0'")
        self.prefab.core.run("uci set firewall.@forwarding[1]=forwarding")
        self.prefab.core.run("uci set firewall.@forwarding[1].dest='lan'")
        self.prefab.core.run("uci set firewall.@forwarding[1].src='zerotier'")
        self.prefab.core.run("uci set firewall.@forwarding[2]=forwarding")
        self.prefab.core.run("uci set firewall.@forwarding[2].dest='zerotier'")
        self.prefab.core.run("uci set firewall.@forwarding[2].src='lan'")
        self.prefab.core.run("uci commit")
        
        self.doneset("install")