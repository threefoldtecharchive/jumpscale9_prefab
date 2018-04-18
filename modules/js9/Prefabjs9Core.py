from js9 import j

app = j.tools.prefab._getBaseAppClass()


class Prefabjs9Core(app):
    NAME = 'js9'

    def install(self, reset=False, branch='development', full=False):
        """Install js9 core
        Keyword Arguments:
            reset {bool} -- force install if js9core was already installed (default: {False})
            branch {string} -- branch from which js9core will be installed (default: {'master'})
            full {bool} -- False for production installs and True for development installs
        Example:
            j.tools.prefab.local.js9.js9Core.install()

            or from bash

            js9_prefab local 'js9.js9core.install(reset=True)'
        """
        if self.doneCheck("install", reset):
            return

        if full:
            self.prefab.system.base.development()
        else:
            self.prefab.system.base.install()

        self.bashtools()

        self._base()

        self.prefab.runtimes.pip.doneSet("ensure")  # pip is installed in above

        self.logger.info("js9_install")
        self.core.run("export JS9BRANCH=%s;ZInstall_host_js9" % branch, profile=True)

        self.prefab.runtimes.pip.install("Cython,asyncssh,numpy,python-jose,PyNaCl,PyJWT,fakeredis,pudb,serial")

        self.doneSet("install")

    def bashtools(self, reset=False):

        if self.doneCheck("bashtools", reset):
            return

        S = """
        echo "INSTALL BASHTOOLS"
        curl https://raw.githubusercontent.com/Jumpscale/bash/master/install.sh?$RANDOM > /tmp/install.sh
        bash /tmp/install.sh
        """

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
