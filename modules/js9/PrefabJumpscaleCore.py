from jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabJumpscaleCore(app):
    NAME = 'jumpscale'

    def install(self, reset=False, branch='development', full=False):
        """Install jumpscale core
        Keyword Arguments:
            reset {bool} -- force install if jumpscalecore was already installed (default: {False})
            branch {string} -- branch from which jumpscalecore will be installed (default: {'master'})
            full {bool} -- False for production installs and True for development installs
        Example:
            j.tools.prefab.local.jumpscale.jumpscaleCore.install()

            or from bash

            js_prefab local 'jumpscale.jumpscalecore.install(reset=True)'
        """
        if self.doneCheck("install", reset):
            return

        if full:
            self.prefab.system.base.development()
        else:
            self.prefab.system.base.install()

        self.bashtools(branch)

        self._base()

        self.prefab.runtimes.pip.doneSet("ensure")  # pip is installed in above

        self.logger.info("jumpscale_install")

        self.core.run("export JUMPSCALEBRANCH=%s;ZInstall_host_jumpscale" % branch, profile=True)

        
        self.doneSet("install")

    def bashtools(self, branch='master', reset=False):

        if self.doneCheck("bashtools", reset):
            return

        S = """
        echo "INSTALL BASHTOOLS"
        curl https://raw.githubusercontent.com/Jumpscale/bash/{}/install.sh?$RANDOM > /tmp/install.sh
        bash /tmp/install.sh
        """.format(branch)

        self.core.execute_bash(S)
        path = j.sal.fs.joinPaths(j.dirs.CODEDIR, 'github', 'jumpscale', 'bash', 'zlibs.sh')
        self.prefab.bash.profileJS.addInclude(path)
        self.prefab.bash.profileJS.save()

        self.doneSet("bashtools")

    def _base(self, reset=False):

        if self.doneCheck("base", reset):
            return

        self.core.run("ZInstall_host_base", profile=True)

        self.doneSet("base")
