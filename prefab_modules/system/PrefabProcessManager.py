
from ProcessManager import PrefabRunit, PrefabTmuxec, PrefabSystemd
from Jumpscale import j

base = j.tools.prefab._BaseClass

class PrefabProcessManager(base):

    def _init(self):
        self.pms = {}


    def systemdOK(self):
        res =  self.prefab.core.command_check("systemctl")
        self._logger.info("systemd:%s" % res)
        return res

    def svOK(self):
        res = self.prefab.core.command_check("sv")
        self._logger.info("systemd:%s" % res)
        return res

    def get_prefered(self):
        #TODO : this will always return tmux, it should check other pms first
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
        """gets a process manager prefab you can choose the process manager type like this:
        Tmux: prefab.system.processmanager.get(pm='tmux') 
        Runit: prefab.system.processmanager.get(pm='sv') 
        SystemD: prefab.system.processmanager.get(pm='tmux') 
        
        if pm=None, prefab will try to get your prefered process manager
            by checking what pm is available 
        
        :param pm: process manager or none to let prefab select your prefered process manager, defaults to None
        :param pm: String, optional
        :return: process manager to be used
        :rtype: Process manager
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
