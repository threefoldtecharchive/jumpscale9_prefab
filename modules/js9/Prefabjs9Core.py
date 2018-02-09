from js9 import j

app = j.tools.prefab._getBaseAppClass()


class Prefabjs9Core(app):
    NAME = 'js9'

    def install(self, reset=False, branch='9.3.0_ssh',full=False):
        """Install js9 core
        Keyword Arguments:
            reset {bool} -- force install if js9core was already installed (default: {False})
            branch {string} -- branch from which js9core will be installed (default: {'master'})
        Example:
            j.tools.prefab.local.js9.js9Core.install()

            or from bash

            js9_prefab local 'js9.js9core.install(reset=True)'
        """
        if self.doneCheck("install", reset):
            return

        if full:
            self.prefab.system.base.development()

        self.bashtools()

        self._base()

        self.prefab.runtimes.pip.doneSet("ensure")  # pip is installed in above

        self.logger.info("js9_install")
        self.core.run(
            "export JS9BRANCH=%s;ZInstall_host_js9" % branch, profile=True)

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

        self.doneSet("bashtools")

    def _base(self, reset=False):

        if self.doneCheck("base", reset):
            return

        self.core.run("ZInstall_host_base", profile=True)

        self.doneSet("base")
