
from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineUFW(base):

    def _init(self):
        self._ufw_allow = {}
        self._ufw_deny = {}
        self._ufw_enabled = None

    @property
    def ufw_enabled(self):
        if not self._ufw_enabled:
            if not self.cuisine.core.isMac:
                if self.cuisine.bash.cmdGetPath("nft", die=False) is not False:
                    self._ufw_enabled = False
                    self.logger.info("cannot use ufw, nft installed")
                if self.cuisine.bash.cmdGetPath("ufw", die=False) is False:
                    self.cuisine.package.install("ufw")
                    self.cuisine.bash.cmdGetPath("ufw")
                self._ufw_enabled = "inactive" not in self.cuisine.core.run("ufw status")[1]
        return self._ufw_enabled

    def ufw_enable(self):
        if not self.ufw_enabled:
            if not self.cuisine.core.isMac:
                if self.cuisine.bash.cmdGetPath("nft", die=False) is not False:
                    self._fw_enabled = False
                    raise j.exceptions.RuntimeError("Cannot use ufw, nft installed")
                if self.executor.type != 'local':
                    self.cuisine.core.run("ufw allow %s" % self.executor.port)
                self.cuisine.core.run("echo \"y\" | ufw enable")
                self._fw_enabled = True
                return True
            raise j.exceptions.Input(message="cannot enable ufw, not supported or ",
                                     level=1, source="", tags="", msgpub="")
        return True

    @property
    def ufw_rules_allow(self):
        if self.cuisine.core.isMac:
            return {}
        if self._ufw_allow == {}:
            self._ufw_status()
        return self._ufw_allow

    @property
    def ufw_rules_deny(self):
        if self.cuisine.core.isMac:
            return {}
        if self._ufw_deny == {}:
            self._ufw_status()
        return self._ufw_deny

    def _ufw_status(self):
        self.ufw_enable()
        _, out, _ = self.cuisine.core.run("ufw status")
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
        if self.cuisine.core.isMac:
            return
        self.ufw_enable()
        self.cuisine.core.run("ufw allow %s/%s" % (port, protocol))

    def denyIncoming(self, port):
        if self.cuisine.core.isMac:
            return

        self.ufw_enable()
        self.cuisine.core.run("ufw deny %s" % port)

    def flush(self):
        C = """
        ufw disable
        iptables --flush
        iptables --delete-chain
        iptables --table nat --flush
        iptables --table filter --flush
        iptables --table nat --delete-chain
        iptables --table filter --delete-chain
        """
        self.cuisine.core.execute_bash(C)

    def show(self):
        a = self.ufw_rules_allow
        b = self.ufw_rules_deny
        self.logger.info("ALLOW")
        self.logger.info(a)
        self.logger.info("DENY")
        self.logger.info(b)

        # self.logger.info(self.cuisine.core.run("iptables -t nat -nvL"))
