
from processManager import PrefabRunit, PrefabTmuxec, PrefabSystemd
from js9 import j

base = j.tools.prefab._getBaseClass()

class PrefabprocessManager(base):

    def _init(self):
        self.pms = {}
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get("processManagerfactory")
        return self._logger

    def systemdOK(self):
        res = not self.prefab.core.isDocker and self.prefab.core.command_check("systemctl")
        self.logger.info("systemd:%s" % res)
        return res

    def svOK(self):
        res = self.prefab.core.command_check("sv")
        self.logger.info("systemd:%s" % res)
        return res

    def get_prefered(self):
        for pm in ["tmux", "systemd", "sv"]:
            if self.is_available(pm):
                return pm

    def is_available(self, pm):
        if pm == "systemd":
            return self.systemdOK()
        elif pm == "sv":
            return self.svOK()
        elif pm == "tmux":
            return True
        else:
            return False

    def get(self, pm=None):
        """
        pm is tmux, systemd or sv
        (sv=runit)
        """
        if pm is None:
            pm = self.get_prefered()
        else:
            if not self.is_available(pm):
                return j.errorhandler.raiseCritical('%s processManager is not available on your system' % (pm))

        if pm not in self.pms:
            if pm == "systemd":
                inst = PrefabSystemd(self.prefab.core.executor, self.prefab)
            elif pm == "sv":
                inst = PrefabRunit(self.prefab.core.executor, self.prefab)
            elif pm == "tmux":
                inst = PrefabTmuxec(self.prefab.core.executor, self.prefab)
            self.pms[pm] = inst

        return self.pms[pm]
