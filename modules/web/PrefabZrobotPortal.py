from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZrobotPortal(base):

    def install(self, branch="master", dest=None, start_portal=True, reset=False):
        if self.doneCheck("install", reset):
            return

        self.prefab.tools.git.pullRepo('https://github.com/zero-os/0-robot-portal', dest=dest, branch=branch)
        portal_config = self.executor.state.configGet('portal')
        if dest:
           app_dir = dest + '/apps'
        else:
            app_dir = "{}/github/zero-os/0-robot-portal/apps".format(j.dirs.CODEDIR)

        portal_config['main']['contentdirs'] = app_dir
        self.executor.state.configSet('portal', portal_config, save=True)
        if start_portal:
            self.prefab.web.portal.start()

        self.doneSet("install")