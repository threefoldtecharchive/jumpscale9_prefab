
from jumpscale import j
from netaddr import IPAddress
import re

base = j.tools.prefab._getBaseClass()


class PrefabNet(base):

    def netconfig(self, interface, ipaddr, cidr=24, gateway=None, dns="8.8.8.8", masquerading=False,
                  dhcp=False):
        conf = """
        [Match]
        Name={interface}

        [Network]
        DNS={dns}
        Address={ipaddr}/{cidr}
        Gateway={gateway}
        IPForward={ipmasquerade}
        IPMasquerade={ipmasquerade}
        """.format(interface=interface, ipaddr=ipaddr, dns=dns, cidr=cidr, gateway=gateway,
                   ipmasquerade=("yes" if masquerading else "no"), dhcp=("yes" if dhcp else "no"))

        targetfile = '/etc/systemd/network/{interface}.network'.format(interface=interface)
        self.prefab.core.file_write(targetfile, content=conf)
        if masquerading:
            # TODO: check if the rule exists
            self.prefab.core.run('iptables -t nat -A POSTROUTING -s {ipaddr}/{cidr} ! -d \
                              {ipaddr}/{cidr} -j MASQUERADE'.format(ipaddr=ipaddr, cidr=cidr))
            self.prefab.system.package.install('iptables-persistent')
            self.prefab.core.run('iptables-save > /etc/iptables/rules.v4')
            self.prefab.core.run('ip6tables-save > /etc/iptables/rules.v6')

    @property
    def nics(self):
        res = []
        for item in self.getInfo():
            if item["name"] not in ["lo"]:
                res.append(item["name"])
        return res

    @property
    def ips(self):
        res = []
        for item in self.getInfo():
            if item["name"] not in ["lo"]:
                for ip in item["ip"]:
                    if ip not in res:
                        res.append(ip)
        return res

    @property
    def defaultgw(self):
        out = self.prefab.core.run("ip r | grep 'default'")[1]
        return out.split(" ")[2]

    @property
    def defaultgwInterface(self):
        """
        returns device over which default gateway goes
        """
        out = self.prefab.core.run("ip r | grep 'default'", showout=False)[1]
        return out.split(" ")[4]

    @defaultgw.setter
    def defaultgw(self, val):
        raise j.exceptions.RuntimeError("not implemented")

    @property
    def wirelessLanInterfaces(self):
        """
        find which wireless interfaces exist
        """
        cmd = "for i in /sys/class/net/*; do ls $i/wireless 2> /dev/null && basename $i; done"
        out = self.prefab.core.run(cmd, showout=False)[1]
        return out.split("\n")

    def findNodesSSH(self, range=None, ips=[]):
        """
        @param range in format 192.168.0.0/24

        if range not specified then will take all ranges of local ip addresses (nics)
        find nodes which are active around (answer on SSH)

        """
        if range is None:
            res = self.prefab.system.net.getInfo()
            for item in res:
                cidr = item['cidr']

                name = item['name']
                if not name.startswith("docker") and name not in ["lo"]:
                    if len(item['ip']) > 0:
                        ip = item['ip'][0]
                        ipn = netaddr.IPNetwork(ip + "/" + str(cidr))
                        range = str(ipn.network) + "/%s" % cidr
                        ips = self.findnodes(range, ips)
            return ips
        else:
            try:
                _, out, _ = self.prefab.core.run(
                    "nmap %s -n -sP | grep report | awk '{print $5}'" % range, showout=False)
            except Exception as e:
                if str(e).find("command not found") != -1:
                    self.prefab.system.package.install("nmap")
                    _, out, _ = self.prefab.core.run(
                        "nmap %s -n -sP | grep report | awk '{print $5}'" % range, showout=False)
            for line in out.splitlines():
                ip = line.strip()
                if ip not in ips:
                    ips.append(ip)
            return ips

    def _getNetworkInfoLinux(self, device=None):
        """
        returns network info like

        [{'cidr': 8, 'ip': ['127.0.0.1'], 'mac': '00:00:00:00:00:00', 'name': 'lo'},
         {'cidr': 24,
          'ip': ['192.168.0.105'],
          'mac': '80:ee:73:a9:19:05',
          'name': 'enp2s0'},
         {'cidr': 0, 'ip': [], 'mac': '80:ee:73:a9:19:06', 'name': 'enp3s0'},
         {'cidr': 16,
          'ip': ['172.17.0.1'],
          'mac': '02:42:97:63:e6:ba',
          'name': 'docker0'}]

        """
       
        IPBLOCKS = re.compile("(^|\n)(?P<block>\d+:.*?)(?=(\n\d+)|$)", re.S)
        IPMAC = re.compile("^\s+link/\w+\s+(?P<mac>(\w+:){5}\w{2})", re.M)
        IPIP = re.compile(r"\s+?inet\s(?P<ip>(\d+\.){3}\d+)/(?P<cidr>\d+)", re.M)
        IPNAME = re.compile("^\d+: (?P<name>.*?)(?=:)", re.M)

        def parseBlock(block):
            result = {'ip': [],'ip6': [], 'cidr': [], 'mac': '', 'name': ''}
            for rec in (IPMAC, IPNAME):
                match = rec.search(block)
                if match:
                    result.update(match.groupdict())
            for mrec in (IPIP, ):
                for m in mrec.finditer(block):
                    for key, value in list(m.groupdict().items()):
                        result[key].append(value)
            _,IPV6,_=self.prefab.core.run("ifconfig %s |  awk '/inet6/{print $2}'"% result['name'], showout=False)
            for ipv6 in IPV6.split('\n'):
                result['ip6'].append(ipv6)
            if j.data.types.list.check(result['cidr']):
                if len(result['cidr']) == 0:
                    result['cidr'] = 0
                else:
                    result['cidr'] = int(result['cidr'][0])
            return result

        def getNetworkInfo():
            _, output, _ = self.prefab.core.run("ip a", showout=False)
            for m in IPBLOCKS.finditer(output):
                block = m.group('block')
                yield parseBlock(block)

        res = []
        for nic in getNetworkInfo():
            # self.logger.info(nic["name"])
            if nic["name"] == device:
                return nic
            res.append(nic)

        if device is not None:
            raise j.exceptions.RuntimeError("could not find device")
        return res
        
    def _getNetworkInfoOSX(self):
        
        #TODO: KEEP AS STATE MACHINE, DO NOT GO TO REGEX, this is much easier to read & change
        #TODO: has not been tested nor finished
        
        
        _, output, _ = j.sal.process.execute("ifconfig", showout=False)
        state="start"
        interfaces = []
        result = {'name': ''} #starting one
        for line in output.split("\n"):
            line_strip = line.strip()
            if line.strip()=="":
                continue
            if line[0] is not " ":
                if line.startswith("lo"):
                    continue               

                if "BROADCAST" in line:
                    #then ok network to parse
                    result = {'ip': [], 'mac': '', 'name': '', 'active':False, 'ip6': [], 'cidr': [] }
                    result["name"]=line.split(":",1)[0].strip()
                    state = "block"
                    
            if state == "block":
                if line_strip.startswith("ether"):
                    result["mac"] = line_strip.split(" ",1)[1].strip()
                elif line_strip.startswith("inet6"):                    
                    ip6 = line_strip[6:].split("prefixlen",1)[0].strip()
                    if ip6 not in result["ip6"]:
                        result["ip6"].append(ip6)
                elif line_strip.startswith("inet "):                    
                    ip = line_strip[5:].split("netmask",1)[0].strip()     
                    line0 = line_strip.split("netmask",1)[1].strip()
                    mask = line0.split("broadcast",1)[0].strip()     
                    cidr = IPAddress(mask).netmask_bits()
                    if cidr not in result["cidr"]:
                        result["cidr"].append(cidr)
                    if ip not in result["ip"]:
                        result["ip"].append(ip)
                    if ip not in result["ip"]:
                        result["ip"].append(ip)
                elif line_strip.startswith("status"):
                    if "inactive" in line:
                        result["active"]=False
                    else:
                        result["active"]=True
                    interfaces.append(result)
                             
        return interfaces
        
    def getInfo(self, device=None):
        """
        returns network info like

        [{'cidr': 8, 'ip': ['127.0.0.1'], 'mac': '00:00:00:00:00:00', 'name': 'lo'},
         {'cidr': 24,
          'ip': ['192.168.0.105'],
          'ip6': ['...','...],
          'mac': '80:ee:73:a9:19:05',
          'name': 'enp2s0'},
         {'cidr': 0, 'ip': [], 'mac': '80:ee:73:a9:19:06', 'name': 'enp3s0'},
         {'cidr': 16,
          'ip': ['172.17.0.1'],
          'mac': '02:42:97:63:e6:ba',
          'name': 'docker0'}]

        """
        if j.core.platformtype.myplatform.isLinux:
            return self._getNetworkInfoLinux()
        elif j.core.platformtype.myplatform.isMac:
            return self._getNetworkInfoOSX()
        else:
            raise RuntimeError("not implemented")


        if device is not None:
            raise j.exceptions.RuntimeError("not implemented")

    def getNetObject(self, device):
        n = self.getInfo(device)
        net = netaddr.IPNetwork(n["ip"][0] + "/" + str(n["cidr"]))
        return net.cidr

    def getNetRange(self, device, skipBegin=10, skipEnd=10):
        """
        return ($fromip,$topip) from range attached to device, skip the mentioned ip addresses
        """
        n = self.getNetObject(device)
        return(str(netaddr.IPAddress(n.first + skipBegin)), str(netaddr.IPAddress(n.last - skipEnd)))

    def ping(self, host):
        rc, out, err = self.prefab.core.run("ping -c 1 %s" % host, die=False, showout=False)
        if rc != 0:
            return False
        return True

    def setInterfaceFile(self, ifacefile, pinghost="www.google.com"):
        """
        will set interface file, if network access goes away then will restore previous one
        """

        if not self.ping(pinghost):
            raise j.exceptions.Input(
                message="Cannot set interface if we cannot ping to the host we have to check against.",
                level=1,
                source="",
                tags="",
                msgpub="")

        pscript = """
        C='''
        $ifacefile
        '''
        import os

        rc=os.system("cp /etc/network/interfaces /etc/network/interfaces_old")
        if rc>0:
            raise RuntimeError("Cannot make copy of interfaces file")

        f = open('/etc/network/interfaces', 'w')
        f.write(C)

        # now applying
        self.logger.info("restart network")
        rc=os.system("/etc/init.d/networking restart")
        rc=os.system("/etc/init.d/networking restart")
        self.logger.info("restart network done")

        rc=os.system("ping -c 1 $pinghost")
        rc2=0

        if rc!=0:
            # could not ping need to restore
            os.system("cp /etc/network/interfaces_old /etc/network/interfaces")

            self.logger.info("restart network to recover")
            rc2=os.system("/etc/init.d/networking restart")
            rc2=os.system("/etc/init.d/networking restart")
            self.logger.info("restart done to recover")

        if rc>0 or rc2>0:
            raise RuntimeError("Could not set interface file, something went wrong, previous situation restored.")
        """
        pscript = j.data.text.strip(pscript)
        pscript = pscript.replace("$ifacefile", ifacefile)
        pscript = pscript.replace("$pinghost", pinghost)

        self.logger.info(pscript)

        self.prefab.core.execute_bash(content=pscript, die=True, interpreter="python3", tmux=True)
        