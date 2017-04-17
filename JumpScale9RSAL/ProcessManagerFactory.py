
from JumpScale.tools.cuisine.CuisineProcessManager import CuisineRunit, CuisineTmuxec, CuisineSystemd
from JumpScale import j


class ProcessManagerFactory:

    def __init__(self, cuisine):
        self.pms = {}
        self._cuisine = cuisine
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get("processmanagerfactory")
        return self._logger


    def systemdOK(self):
        res = not self._cuisine.core.isDocker and self._cuisine.core.command_check("systemctl")
        self.logger.info("systemd:%s" % res)
        return res

    def svOK(self):
        res = self._cuisine.core.command_check("sv")
        self.logger.info("systemd:%s" % res)
        return res

    def get_prefered(self):
        for pm in ["tmux","systemd", "sv"]:
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
                inst = CuisineSystemd(self._cuisine.core.executor, self._cuisine)
            elif pm == "sv":
                inst = CuisineRunit(self._cuisine.core.executor, self._cuisine)
            elif pm == "tmux":
                inst = CuisineTmuxec(self._cuisine.core.executor, self._cuisine)
            self.pms[pm] = inst

        return self.pms[pm]
