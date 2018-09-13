
from Jumpscale import j
import time

base = j.tools.prefab._getBaseClass()


class PrefabInstallBase(base):
    """
    the base for any install
    """

    def install(self, reset=False, upgrade=True):

        if self.doneCheck("install", reset):
            return

        self.upgrade()

        if not self.doneCheck("fixlocale", reset):
            self.prefab.bash.locale_check()
            self.doneSet("fixlocale")

        out = ""
        # make sure all dirs exist
        for key, item in self.prefab.core.dir_paths.items():
            out += "mkdir -p %s\n" % item
        self.prefab.core.execute_bash(out)

        self.prefab.system.package.mdupdate()

        # if not self.prefab.core.isMac and not self.prefab.core.isCygwin:
        #     self.prefab.system.package.install("fuse")

        if self.prefab.core.isArch:
            # is for wireless auto start capability
            self.prefab.system.package.install("wpa_actiond,redis-server")

        if self.prefab.core.isMac:
            C = ""
        else:
            C = """
            sudo
            net-tools
            python3
            """

        C += """
        openssl
        wget
        curl
        git
        mc
        tmux
        rsync
        """
        self.prefab.system.package.install(C)

        self.prefab.bash.profileJS.addPath(j.sal.fs.joinPaths(
            self.prefab.core.dir_paths["BASEDIR"], "bin"))
        self.prefab.bash.profileJS.save()

        if upgrade:
            self.upgrade(reset=reset, update=False)

        self.doneSet("install")

    def development(self,reset=False,python=True):
        """
        install all components required for building (compiling)
        """

        C = """
        autoconf        
        gcc
        make        
        autoconf
        libtool
        pkg-config
        """
        C=j.core.text.strip(C)

        if self.core.isMac:
            C+="libffi\n"
            C+="automake\n"
        else:
            C+="libffi-dev\n"
            C+="build-essential\n"
            C+="libsqlite3-dev\n"
            C+="libpq-dev\n"
        
        if python:
            C+="python3-dev\n"

        self.install()
        if self.doneCheck("development", reset):
            return        
        self.prefab.system.package.install(C)   
        self.doneSet("development")     

    def upgrade(self, reset=False, update=True):
        if self.doneCheck("upgrade", reset):
            return
        if update:
            self.prefab.system.package.mdupdate(reset=reset)
        self.prefab.system.package.upgrade(reset=reset)
        self.prefab.system.package.clean()

        self.doneSet("upgrade")
