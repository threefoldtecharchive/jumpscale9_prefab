from js9 import j


class Avahi:

    def __init__(self):
        self.__jslocation__ = "j.tools.avahi"
        self._prefab = j.tools.prefab.get()
        self.executor = self._prefab._executor

    def get(self, prefab, executor):
        b = Avahi()
        b.prefab = prefab
        b.executor = executor
        return b

    def install(self):
        if self._prefab.core.isUbuntu:
            self._prefab.package.install("avahi-daemon")
            self._prefab.package.install("avahi-utils")
        if self._prefab.core.isArch:
            self._prefab.package.install("avahi")

        configfile = "/etc/avahi/avahi-daemon.conf"

        C = """
        [server]
        host-name=$hostname
        domain-name=$domains
        browse-domains=$domains
        use-ipv4=yes
        use-ipv6=no
        #allow-interfaces=eth0
        #deny-interfaces=eth1
        #check-response-ttl=no
        #use-iff-running=no
        #enable-dbus=yes
        #disallow-other-stacks=no
        #allow-point-to-point=no
        #cache-entries-max=4096
        #clients-max=4096
        #objects-per-client-max=1024
        #entries-per-entry-group-max=32
        ratelimit-interval-usec=1000000
        ratelimit-burst=1000

        [wide-area]
        #enable-wide-area=yes

        [publish]
        #disable-publishing=no
        #disable-user-service-publishing=no
        #add-service-cookie=no
        publish-addresses=yes
        publish-hinfo=yes
        publish-workstation=yes
        publish-domain=yes
        publish-dns-servers=8.8.8.8
        publish-resolv-conf-dns-servers=yes
        publish-aaaa-on-ipv4=yes
        #publish-a-on-ipv6=no

        [reflector]
        #enable-reflector=no
        #reflect-ipv=no

        [rlimits]
        #rlimit-as=
        rlimit-core=0
        rlimit-data=4194304
        rlimit-fsize=0
        rlimit-nofile=768
        rlimit-stack=4194304
        rlimit-nproc=3
        """
        domains = "%s.%s" % (self._prefab.grid, self._prefab.domain)
        C = C.replace("$hostname", self._prefab.core.name)
        C = C.replace("$domains", domains)
        self._prefab.core.file_write(configfile, C)

        if self._prefab.core.isUbuntu:
            pre = ""
        else:
            pre = "/usr"
        self._prefab.core.file_link(
            source="%s/lib/systemd/system/avahi-daemon.service",
            destination="/etc/systemd/system/multi-user.target.wants/avahi-daemon.service",
            symbolic=True,
            mode=None,
            owner=None,
            group=None)
        self._prefab.core.file_link(
            source="%s/lib/systemd/system/docker.socket",
            destination="/etc/systemd/system/sockets.target.wants/docker.socket",
            symbolic=True,
            mode=None,
            owner=None,
            group=None)

        self._prefab.systemd.start("avahi-daemon")

    def _servicePath(self, servicename):
        path = "/etc/avahi/services"
        if not self._prefab.core.dir_exists(path):
            self._prefab.core.dir_ensure(path)
        service = '%s.service' % servicename
        return j.sal.fs.joinPaths(path, service)

    def registerService(self, servicename, port, type='tcp'):
        content = """<?xml version=\"1.0\" standalone=\'no\'?>
<!--*-nxml-*-->
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<!-- $Id$ -->
<service-group>
<name replace-wildcards="yes">${servicename} %h</name>

<service protocol="ipv4">
    <type>_${servicename}._${type}</type>
    <port>${port}</port>
</service>

</service-group>
"""
        content = content.replace("${servicename}", servicename)
        content = content.replace("${port}", str(port))
        content = content.replace("${type}", type)
        path = self._servicePath(servicename)
        self._prefab.core.file_write(path, content)

        self.reload()

    def reload(self):
        cmd = "avahi-daemon --reload"
        self._prefab.core.run(cmd)

    def removeService(self, servicename):
        path = self._servicePath(servicename)
        # if self._prefab.core.dir_exists(path=path):
        self._prefab.core.dir_remove(path)
        self.reload()

    def getServices(self):
        cmd = "avahi-browse -a -r -t"
        result, output, err = self._prefab.core.run(cmd, die=False, force=True)
        if result > 0:
            raise j.exceptions.RuntimeError(
                "cannot use avahi command line to find services, please check avahi is installed on system (ubunutu apt-get install avahi-utils)\nCmd Used:%s" %
                cmd)
        items = j.tools.code.regex.extractBlocks(output, ["^= .*"])
        avahiservices = AvahiServices()
        for item in items:
            s = AvahiService()
            lineitems = item.split("\n")[0][1:].strip().split("  ")
            lineitemsout = []
            for lineitem in lineitems:
                if lineitem.strip() != "":
                    lineitemsout.append(lineitem.strip())
            if len(lineitemsout) == 3:
                s.description, s.servicename, s.domain = lineitemsout
            if len(lineitemsout) == 2:
                s.description, s.servicename = lineitemsout
                s.domain = ""
            if len(lineitemsout) < 2 or len(lineitemsout) > 3:
                s.servicename = lineitemsout[0]

            s.hostname = j.tools.code.regex.getINIAlikeVariableFromText(
                " *hostname *", item).replace("[", "").replace("]", "").strip()
            s.address = j.tools.code.regex.getINIAlikeVariableFromText(
                " *address *", item).replace("[", "").replace("]", "").strip()
            s.port = j.tools.code.regex.getINIAlikeVariableFromText(
                " *port *", item).replace("[", "").replace("]", "").strip()
            s.txt = j.tools.code.regex.getINIAlikeVariableFromText(
                " *txt *", item).replace("[", "").replace("]", "").strip()
            avahiservices._add(s)
        return avahiservices

    def resolveAddress(self, ipAddress):
        """
        Resolve the ip address to its hostname

        @param ipAddress: the ip address to resolve
        @type ipAddress: string

        @return: the hostname attached to the ip address
        """
        # do some validation
        if not j.sal.nettools.validateIpAddress(ipAddress):
            raise ValueError('Invalid Ip Address')
        cmd = 'avahi-resolve-address %s'
        rc, out, err = self._prefab.core.run(cmd % ipAddress, die=False, showout=False)
        if rc or not out:  # if the ouput string is '' then something is wrong
            raise j.exceptions.RuntimeError('Cannot resolve the hostname of ipaddress: %s' % ipAddress)
        out = out.strip()
        hostname = out.split('\t')[-1]
        # remove the trailing .local
        hostname = hostname.replace('.local', '')
        return hostname


class AvahiServices:

    def __init__(self):
        self.services = []

    def _add(self, service):
        self.services.append(service)

    def exists(self, hostname="", partofname="", partofdescription="", port=0):
        """
        @return True/False,resultOfServices   #avoids having to wait twice for avahi query
        """
        res = self.find(hostname, partofname, partofdescription, port)
        return (len(res) > 0, res)

    def find(self, hostname="", partofname="", partofdescription="", port=0):
        def check1(service, hostname):
            if hostname != "" and service.hostname.lower().strip() == hostname.lower().strip():
                return True
            if hostname == "":
                return True
            return False

        def check4(service, partofname):
            if partofname != "" and service.servicename.find(partofname) > -1:
                return True
            if partofname == "":
                return True
            return False

        def check2(service, partofdescription):
            if partofdescription != "" and service.description.find(partofdescription) > -1:
                return True
            if partofdescription == "":
                return True
            return False

        def check3(service, port):
            if int(port) != 0 and int(service.port) == int(port):
                return True
            if int(port) == 0:
                return True
            return False
        result = []
        for service in self.services:
            if check1(service, hostname) and check2(service, partofdescription) and check3(
                    service, port) and check4(service, partofname):
                result.append(service)
        return result

    def __str__(self):
        txt = ""
        for item in self.services:
            txt = "%s%s\n" % (txt, item)
        return txt

    def __repr__(self):
        return self.__str__()


class AvahiService:

    def __init__(self):
        self.servicename = ""
        self.hostname = ""
        self.address = ""
        self.port = 0
        self.txt = ""
        self.description = ""
        self.domain = ""

    def __str__(self):
        return "descr:%s name:%s hostname:%s address:%s port:%s" % (
            self.description, self.servicename, self.hostname, self.address, self.port)

    def __repr__(self):
        return self.__str__()
