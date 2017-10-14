from js9 import j

app = j.tools.prefab._getBaseAppClass()


class Prefabjs9Core(app):
    NAME = 'js9'

    def install(self, reset=False):
        """
        j.tools.prefab.local.js9.js9Core.install()

        or from bash

        js9_prefab local 'js9.js9core.install(reset=1)'

        """
        if self.doneCheck("install", reset):
            return

        self.prefab.system.base.install()

        self.bashtools()

        print(554678)
        from IPython import embed
        embed(colors='Linux')

        self._base()

        self.prefab.runtimes.pip.doneSet("ensure")  # pip is installed in above

        # S = """
        # set +ex
        # source ~/code/github/jumpscale/bash/zlibs.sh 2>&1 > /dev/null
        # source /opt/code/github/jumpscale/bash/zlibs.sh 2>&1 > /dev/null

        # set -e
        # echo "install js9"
        # ZInstall_host_js9 || die "Could not install core9 of js9" || exit 1
        # """
        # self.core.execute_bash(S)

        # self.core.execute("ZInstall_host_js9")

        # self.prefab.runtimes.pip.install("Cython,asyncssh,numpy,tarantool")

        # self.doneSet("install")

        print("js9_install")
        from IPython import embed
        embed(colors='Linux')

    def bashtools(self, reset=False):

        if self.doneCheck("bashtools", reset):
            return

        self.doneSet("bashtools")

        S = """
        echo "INSTALL BASHTOOLS"
        curl https://raw.githubusercontent.com/Jumpscale/bash/master/install.sh?$RANDOM > /tmp/install.sh        
        bash /tmp/install.sh || echo "could not install bash tools" && exit 1
        """

        self.core.execute_bash(S)

        self.doneSet("bashtools")

    def _base(self, reset=False):

        if self.doneCheck("base", reset):
            return

        self.core.execute("ZInstall_host_base")

        self.doneSet("base")
