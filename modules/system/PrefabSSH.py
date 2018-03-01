
from js9 import j
import netaddr


base = j.tools.prefab._getBaseClass()


class PrefabSSH(base):

    def test_login(self, passwd, port=22, range=None, onlyplatform="arch"):
        login = "root"
        res = []
        for item in self.scan(range=range):
            self.logger.info("test for login/passwd on %s" % item)
            try:
                client = j.clients.ssh.new(addr=item, port=port, login=login, passwd=passwd, timeout=1, die=False)
            except Exception as e:
                self.logger.info("  NOT OK")
                continue
            if testoutput is False:
                self.logger.info("  NOT OK")
                continue
            executor = j.tools.executor.getSSHBased(item, port, login, passwd, checkok=True)
            if onlyplatform != "":
                if not str(executor.prefab.platformtype).startswith(onlyplatform):
                    continue
            self.logger.info("  RESPONDED!!!")
            res.append(item)
        return res

    def test_login_pushkey(self, passwd, keyname, port=22, range=None, changepasswdto="", onlyplatform="arch"):
        """
        """
        login = "root"
        done = []
        for item in self.test_login(passwd, port, range, onlyplatform=onlyplatform):
            keypath = j.sal.fs.joinPaths(self.prefab.bash.env["HOME"], ".ssh", keyname + ".pub")
            if j.sal.fs.exists(keypath):
                key = j.sal.fs.fileGetContents(keypath)
                executor = j.tools.executor.getSSHBased(item, port, login, passwd, checkok=True)
                executor.prefab.system.ssh.authorize(user="root", key=key)
                if changepasswdto != "":
                    executor.prefab.system.user.passwd(login, changepasswdto, encrypted_passwd=False)
            else:
                raise j.exceptions.RuntimeError("Cannot find key:%s" % keypath)
            done.append(item)
        return done

    def scan(self, range=None, ips={}, port=22):
        """
        @param range in format 192.168.0.0/24
        if range not specified then will take all ranges of local ip addresses (nics)
        """
        if not range:
            res = self.prefab.system.net.get_info()
            for item in res:
                cidr = item['cidr']

                name = item['name']
                if not name.startswith("docker") and name not in ["lo"]:
                    if len(item['ip']) > 0:
                        ip = item['ip'][0]
                        ipn = netaddr.IPNetwork(ip + "/" + str(cidr))
                        range = str(ipn.network) + "/%s" % cidr
                        ips = self.scan(range, ips)
            return ips
        else:
            try:
                # out=self.prefab.core.run("nmap -p 22 %s | grep for"%range,showout=False)
                _, out, _ = self.prefab.core.run("nmap %s -p %s --open -oX $TMPDIR/nmap" %
                                                 (range))
            except Exception as e:
                if str(e).find("command not found") != -1:
                    self.prefab.system.package.install("nmap")
                    # out=self.prefab.core.run("nmap -p 22 %s | grep for"%range)
                    _, out, _ = self.prefab.core.run("nmap %s -p %s --open -oX $TMPDIR/nmap" %
                                                     (range))
            out = self.prefab.core.file_read("$TMPDIR/nmap")
            import xml.etree.ElementTree as ET
            root = ET.fromstring(out)
            for child in root:
                if child.tag == "host":
                    ip = None
                    mac = None
                    for addr in child.findall("address"):
                        if addr.get("addrtype") == "ipv4":
                            ip = addr.get("addr")

                    for addr in child.findall("address"):
                        if addr.get("addrtype") == "mac":
                            mac = addr.get("addr")

                    if ip is not None:
                        ips[ip] = {"mac": mac}

            # for line in out.split("\n"):
            #     ip=line.split("for")[1].strip()
            #     if ip.find("(")!=-1:
            #         ip=ip.split("(")[1].strip(")").strip()
            #     if ip not in ips:

            #         ips.append(ip)
            return ips

    def define_host(self, addr, user='root', port=22):
        known_hostsfile = '/{}/.ssh/known_hosts'.format(user)
        lines = self.prefab.core.file_read(known_hostsfile, default='').splitlines()
        isknown = False
        for line in lines:
            if line.startswith(addr):
                isknown = True
                break
        if not isknown:
            self.prefab.core.execute_bash('ssh-keyscan -p {} -t rsa {} >> {}'.format(port, addr, known_hostsfile))

    def keygen(self, user="root", keytype="rsa", name="default"):
        """Generates a pair of ssh keys in the user's home .ssh directory."""
        user = user.strip()
        d = self.prefab.system.user.check(user)
        assert d, "User does not exist: %s" % (user)
        home = d["home"]
        path = '%s/.ssh/%s' % (home, name)
        if not self.prefab.core.file_exists(path + ".pub"):
            self.prefab.core.dir_ensure(home + "/.ssh", mode="0700", owner=user, group=user)

            self.prefab.core.run("ssh-keygen -q -t %s -f %s -N ''" % (keytype, path))
            self.prefab.core.file_attribs(path, mode="0600", owner=user, group=user)
            self.prefab.core.file_attribs("%s.pub" % path, mode="0600", owner=user, group=user)
            return "%s.pub" % path
        else:
            return "%s.pub" % path

    #
    def authorize(self, user, key, **kwargs):
        """
        Adds the given key to the '.ssh/authorized_keys' for the given
        user.

        @param user username to which authorization should be performed
        @param key public ssh key to authorize
        @param kwargs extra settings for this authorization. See https://www.ssh.com/ssh/authorized_keys/openssh
          E.g. setting command option is done by adding the following kwarg: command='"/bin/myscript.sh"
          E.g. setting no-agent-forwarding is done by adding the following kwarg: no-agent-forwarding=True
        """

        def add_newline(content):
            if content and content[-1] != "\n":
                content += "\n"
            return content

        if key is None or key.strip() == "":
            raise j.exceptions.Input("key cannot be empty")
        sudomode = self.prefab.core.sudomode
        self.prefab.core.sudomode = True
        user = user.strip()
        d = self.prefab.system.user.check(user, need_passwd=False)
        if d is None:
            raise j.exceptions.RuntimeError("did not find user:%s" % user)
        group = d["gid"]
        keyf = d["home"] + "/.ssh/authorized_keys"
        key = add_newline(key)
        ret = None

        settings = list()
        for setting, value in kwargs.items():
            if value is True:
                settings.append(setting)
            else:
                settings.append('%s="%s"' % (setting, value))
        if settings:
            line = "%s %s" % (",".join(settings), key)
        else:
            line = key

        if self.prefab.core.file_exists(keyf):
            content = self.prefab.core.file_read(keyf)
            if content.find(key[:-1]) == -1:
                content = add_newline(content)
                self.prefab.core.file_write(keyf, content + line, sudo=True)
                ret = False
            else:
                ret = True
        else:
            # Make sure that .ssh directory exists, see #42
            self.prefab.core.dir_ensure(j.sal.fs.getDirName(keyf), owner=user, group=group, mode="700")
            self.prefab.core.file_write(keyf, line, owner=user, group=group, mode="600", sudo=True)
            ret = False

        self.prefab.core.sudomode = sudomode
        return ret

    def unauthorize(self, user, key):
        """Removes the given key to the remote '.ssh/authorized_keys' for the given
        user."""
        key = key.strip()
        d = self.prefab.system.user.check(user, need_passwd=False)
        group = d["gid"]
        keyf = d["home"] + "/.ssh/authorized_keys"
        if self.prefab.core.file_exists(keyf):
            self.prefab.core.file_write(keyf, "\n".join(_ for _ in self.prefab.core.file_read(keyf).split(
                "\n") if _.strip() != key), owner=user, group=group, mode="600")
            return True
        else:
            return False

    def unauthorizeAll(self):
        """
        """
        self.logger.info("clean known hosts/autorized keys")
        self.prefab.core.dir_ensure("/root/.ssh")
        self.prefab.core.dir_remove("/root/.ssh/known_hosts")
        self.prefab.core.dir_remove("/root/.ssh/authorized_keys")

    def enableAccess(self, keys, backdoorpasswd, backdoorlogin="backdoor", user="root"):
        """
        make sure we can access the environment
        keys are a list of ssh pub keys
        """

        # leave here is to make sure we have a backdoor for when something goes wrong further
        self.logger.info("create backdoor")
        self.prefab.system.user.ensure(backdoorlogin, passwd=backdoorpasswd, home=None, uid=None,
                                       gid=None, shell=None, fullname=None, encrypted_passwd=True, group="root")
        self.prefab.core.run("rm -fr /home/%s/.ssh/" % backdoorlogin)
        self.prefab.system.group.user_add('sudo', '$(system.backdoor.login)')

        self.logger.info("test backdoor")
        j.tools.executor.getSSHBased(addr="$(node.tcp.addr)", port=int("$(ssh.port)"), login="$(system.backdoor.login)",
                                     passwd=passwd, debug=False, checkok=True, allow_agent=False, look_for_keys=False)
        # make sure the backdoor is working
        self.logger.info("backdoor is working (with passwd)")

        self.logger.info("make sure some required packages are installed")
        self.prefab.system.package.install('openssl')
        self.prefab.system.package.install('rsync')

        self.unauthorizeAll()

        for pub in keys:
            if pub.strip() == "":
                raise j.exceptions.RuntimeError("ssh.key.public cannot be empty")
            self.authorize("root", pub)

        self.logger.info("add git repos to known hosts")
        self.prefab.core.run("ssh-keyscan github.com >> /root/.ssh/known_hosts")
        self.prefab.core.run("ssh-keyscan git.aydo.com >> /root/.ssh/known_hosts")

        self.logger.info("enable access done.")

    def sshagent_add(self, path, removeFirst=True):
        """
        @path is path to private key
        """
        self.logger.info("add ssh key to ssh-agent: %s" % path)
        if removeFirst:
            self.prefab.core.run("ssh-add -d '%s'" % path, die=False, showout=False)
            _, keys, _ = self.prefab.core.run("ssh-add -l", die=False, showout=False)
            if path in keys:
                raise j.exceptions.RuntimeError("ssh-key is still loaded in ssh-agent, please remove manually")
        self.prefab.core.run("ssh-add '%s'" % path, showout=False)

    def sshagent_remove(self, path):
        """
        @path is path to private key
        """
        self.logger.info("remove ssh key to ssh-agent: %s" % path)
        self.prefab.core.run("ssh-add -d '%s'" % path, die=False, showout=False)
        _, keys, _ = self.prefab.core.run("ssh-add -l", showout=False)
        if path in keys:
            raise j.exceptions.RuntimeError("ssh-key is still loaded in ssh-agent, please remove manually")

    def __str__(self):
        return "prefab.ssh:%s:%s" % (getattr(self.executor, 'addr', 'local'), getattr(self.executor, 'port', ''))

    __repr__ = __str__
