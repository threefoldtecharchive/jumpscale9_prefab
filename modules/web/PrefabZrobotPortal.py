from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZrobotPortal(base):

    def install(self, branch="master", reset=False):
        if self.doneCheck("install", reset):
            return

        self.prefab.tools.git.pullRepo('https://github.com/zero-os/0-robot-portal', branch=branch)
        portal_config = self.executor.state.configGet('portal')
        portal_config['main']['contentdirs'] = "{}/github/zero-os/0-robot-portal/apps".format(j.dirs.CODEDIR)
        self.executor.state.configSet('portal', portal_config, save=True)
        self.prefab.web.portal.start()

        self.doneSet("install")