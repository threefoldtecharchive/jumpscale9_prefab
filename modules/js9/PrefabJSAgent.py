from js9 import j

app = j.tools.prefab._getBaseAppClass()

# TODO: is this still correct, maybe our docker approach better, need to check


class PrefabJSAgent(app):

    NAME = 'jsagent'

    def build(self):
        raise NotImplementedError()

    def install(self, start=False, gid=1, ctrl_addr='', ctrl_port=4444, ctrl_passwd='', reset=False):
        """
        gid: grid ID
        ctrl_addr: IP address of the controller
        ctrl_port: listening port of the controller
        ctrl_passwd: password of the controller
        """
        if reset is False and self.isInstalled():
            return

        self.prefab.core.dir_ensure('$JSAPPSDIR')
        self.prefab.core.file_link('$CODEDIR/github/threefoldtech/jumpscale_core9/apps/jsagent', '$JSAPPSDIR/jsagent')
        if start is True:
            self.start(gid, ctrl_addr, ctrl_port, ctrl_passwd)

        return

    def start(self, gid, ctrl_addr, ctrl_port=4444, ctrl_passwd=''):
        """
        gid: grid ID
        ctrl_addr: IP address of the controller
        ctrl_port: listening port of the controller
        ctrl_passwd: password of the controller
        """
        cmd = "jspython jsagent.py --grid-id %d --controller-ip %s --controller-port %d" % (gid, ctrl_addr, ctrl_port)
        if ctrl_passwd is not None and ctrl_passwd != '':
            cmd += ' --controller-password %s' % ctrl_passwd
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="jsagent", cmd=cmd, path='$JSAPPSDIR/jsagent')
