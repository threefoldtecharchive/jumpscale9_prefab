
from JumpScale.tools.prefab.PrefabProcessManager import PrefabRunit, PrefabTmuxec, PrefabSystemd
from js9 import j


class ProcessManagerFactory:

    def __init__(self, prefab):
        self.pms = {}
        self._prefab = prefab
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get("processmanagerfactory")
        return self._logger

    def systemdOK(self):
        res = not self._prefab.core.isDocker and self._prefab.core.command_check("systemctl")
        self.logger.info("systemd:%s" % res)
        return res

    def svOK(self):
        res = self._prefab.core.command_check("sv")
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
                return j.errorconditionhandler.raiseCritical('%s processmanager is not available on your system' % (pm))

        if pm not in self.pms:
            if pm == "systemd":
                inst = PrefabSystemd(self._prefab.core.executor, self._prefab)
            elif pm == "sv":
                inst = PrefabRunit(self._prefab.core.executor, self._prefab)
            elif pm == "tmux":
                inst = PrefabTmuxec(self._prefab.core.executor, self._prefab)
            self.pms[pm] = inst

        return self.pms[pm]
