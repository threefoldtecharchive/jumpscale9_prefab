from js9 import j
import time

base = j.tools.prefab._getBaseClass()


class PrefabZeroBoot(base):
    def install(self, network_id, token, reset=False):
        if not reset and self.doneCheck("install"):
            return
        # update zerotier config
        self.prefab.network.zerotier.build(install=True, reset=reset)
        # Start zerotier at least one time to generate config files
        try:
            self.prefab.network.zerotier.start()
        except Exception:
            self.logger.warning("Failed to start zerotier maye it's already started")
        self.prefab.network.zerotier.stop()
        self.prefab.core.run("uci set zerotier.sample_config=zerotier")
        self.prefab.core.run("uci set zerotier.sample_config.enabled='1'")
        self.prefab.core.run("uci set zerotier.sample_config.interface='wan'") # restart ZT when wan status changed
        self.prefab.core.run("uci set zerotier.sample_config.join='{}'".format(network_id)) # Join zerotier network
        self.prefab.core.run("uci set zerotier.sample_config.secret='generate'") # Generate secret on the first start
        self.prefab.core.run("uci commit")
        self.prefab.core.run("/etc/init.d/zerotier enable")
        self.prefab.core.run("/etc/init.d/zerotier start")

        # Join Network
        self.prefab.core.run("zerotier-cli join {network_id}".format(network_id=network_id))

        # Authorize machine into the network
        info_output = self.prefab.core.run("zerotier-cli info")[1]
        machine_address = info_output.split()[2]
        zerotier_cli = j.clients.zerotier.get(data={"token_": token})
        zerotier_cli.client.network.updateMember(address=machine_address, id=network_id,
                                                 data={"config": {"authorized": True}})

        # update TFTP and DHCP
        self.prefab.core.run("uci set dhcp.@dnsmasq[0].enable_tftp='1'")
        self.prefab.core.run("uci set dhcp.@dnsmasq[0].tftp_root='/opt/storage/'")
        self.prefab.core.run("uci set dhcp.@dnsmasq[0].dhcp_boot='pxelinux.0'")
        self.prefab.core.run("uci commit")

        self.prefab.core.dir_ensure('/opt/storage')
        self.prefab.core.run("opkg install curl ca-bundle")
        self.prefab.core.run("curl https://raw.githubusercontent.com/0-complexity/G8_testing/master/pxe.tar.gz -o /opt/storage/pxe.tar.gz")
        self.prefab.core.run("tar -xzf /opt/storage/pxe.tar.gz -C /opt/storage")
        self.prefab.core.run("cp -r /opt/storage/pxe/* /opt/storage")
        self.prefab.core.run("rm -rf /opt/storage/pxe")
        self.prefab.core.run('sed "s|a84ac5c10a670ca3|%s|g" /opt/storage/pxelinux.cfg/default' % network_id)
        time.sleep(30) # this is needed to make sure that network name is ready
        network_name = self.prefab.network.zerotier.network_name_get(network_id)
        self.prefab.core.run("uci set network.{0}=interface".format(network_name))
        self.prefab.core.run("uci set network.{0}.proto='none'".format(network_name))
        self.prefab.core.run("uci set network.{0}.ifname='{0}'".format(network_name))
        self.prefab.core.run("uci set firewall.@zone[2]=zone")
        self.prefab.core.run("uci set firewall.@zone[2].input='ACCEPT'")
        self.prefab.core.run("uci set firewall.@zone[2].output='ACCEPT'")
        self.prefab.core.run("uci set firewall.@zone[2].name='zerotier'")
        self.prefab.core.run("uci set firewall.@zone[2].forward='ACCEPT'")
        self.prefab.core.run("uci set firewall.@zone[2].masq='1'")
        self.prefab.core.run("uci set firewall.@zone[2].network='{0}'".format(network_name))
        self.prefab.core.run("uci add firewall forwarding")
        self.prefab.core.run("uci set firewall.@forwarding[1]=forwarding")
        self.prefab.core.run("uci set firewall.@forwarding[1].dest='lan'")
        self.prefab.core.run("uci set firewall.@forwarding[1].src='zerotier'")
        self.prefab.core.run("uci set firewall.@forwarding[2]=forwarding")
        self.prefab.core.run("uci set firewall.@forwarding[2].dest='zerotier'")
        self.prefab.core.run("uci set firewall.@forwarding[2].src='lan'")
        self.prefab.core.run("uci commit")
        
        self.doneSet("install")