
from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabBase(base):
    """
    the base for any install
    """

    def install(self, reset=False):

        if self.doneGet('install') and reset is False:
            return

        self.prefab.bash.fixlocale()

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
        """
        out = ""
        # make sure all dirs exist
        for key, item in self.prefab.core.dir_paths.items():
            out += "mkdir -p %s\n" % item
        self.prefab.core.execute_bash(out)

        self.prefab.package.mdupdate()

        if not self.prefab.core.isMac and not self.prefab.core.isCygwin:
            self.prefab.package.install("fuse")

        if self.prefab.core.isArch:
            # is for wireless auto start capability
            self.prefab.package.install("wpa_actiond")
            self.prefab.package.install("redis-server")

        self.prefab.package.multiInstall(C)
        self.prefab.package.upgrade()

        self.prefab.package.clean()

        self.prefab.bash.profileJS.addPath(j.sal.fs.joinPaths(
            self.prefab.core.dir_paths["BASEDIR"], "bin"))
        self.prefab.bash.profileJS.save()

        self.doneSet("install")
