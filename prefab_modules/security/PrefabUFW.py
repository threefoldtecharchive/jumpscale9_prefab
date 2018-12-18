
from Jumpscale import j

base = j.tools.prefab._BaseClass


class PrefabUFW(base):

    def _init(self):
        self._ufw_allow = {}
        self._ufw_deny = {}
        self._ufw_enabled = None

    @property
    def ufw_enabled(self):
        if self.prefab.core.isMac:
            return  False        
        if not self._ufw_enabled:
            if not self.prefab.core.isMac:
                if self.prefab.bash.cmdGetPath("nft", die=False) is not False:
                    self._ufw_enabled = False
                    self._logger.info("cannot use ufw, nft installed")
                if self.prefab.bash.cmdGetPath("ufw", die=False) is False:
                    self.prefab.system.package.install("ufw")
                    self.prefab.bash.cmdGetPath("ufw")
                self._ufw_enabled = "inactive" not in self.prefab.core.run("ufw status")[1]
        return self._ufw_enabled

    def ufw_enable(self):
        if not self.ufw_enabled:
            if not self.prefab.core.isMac:
                if self.prefab.bash.cmdGetPath("nft", die=False) is not False:
                    self._fw_enabled = False
                    raise j.exceptions.RuntimeError("Cannot use ufw, nft installed")
                if self.executor.type != 'local':
                    self.prefab.core.run("ufw allow %s" % self.executor.port)
                self.prefab.core.run("echo \"y\" | ufw enable")
                self._fw_enabled = True
                return True
            raise j.exceptions.Input(message="cannot enable ufw, not supported or ",
                                     level=1, source="", tags="", msgpub="")
        return True

    @property
    def ufw_rules_allow(self):
        if self.ufw_enabled == False:
            return {}
        if self._ufw_allow == {}:
            self._ufw_status()
        return self._ufw_allow

    @property
    def ufw_rules_deny(self):
        if self.ufw_enabled == False:
            return {}
        if self._ufw_deny == {}:
            self._ufw_status()
        return self._ufw_deny

    def _ufw_status(self):
        _, out, _ = self.prefab.core.run("ufw status")
        for line in out.splitlines():
            if line.find("(v6)") != -1:
                continue
            if line.find("ALLOW ") != -1:
                ip = line.split(" ", 1)[0]
                self._ufw_allow[ip] = "*"
            if line.find("DENY ") != -1:
                ip = line.split(" ", 1)[0]
                self._ufw_deny[ip] = "*"

    def allowIncoming(self, port, protocol='tcp'):
        if self.ufw_enabled==False:
            return 
        self.prefab.core.run("ufw allow %s/%s" % (port, protocol))

    def denyIncoming(self, port):
        if self.ufw_enabled==False:
            return 
        self.prefab.core.run("ufw deny %s" % port)

    def flush(self):
        if self.ufw_enabled==False:
            return          
        C = """
        ufw disable
        iptables --flush
        iptables --delete-chain
        iptables --table nat --flush
        iptables --table filter --flush
        iptables --table nat --delete-chain
        iptables --table filter --delete-chain
        """
        self.prefab.core.execute_bash(C)

    def show(self):
        if self.ufw_enabled==False:
            return                 
        a = self.ufw_rules_allow
        b = self.ufw_rules_deny
        self._logger.info("ALLOW")
        self._logger.info(a)
        self._logger.info("DENY")
        self._logger.info(b)

        # self._logger.info(self.prefab.core.run("iptables -t nat -nvL"))
