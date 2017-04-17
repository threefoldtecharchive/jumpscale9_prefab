
from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineBase(base):
    """
    the base for any install
    """

    def install(self):
        self.cuisine.bash.fixlocale()

        if self.cuisine.core.isMac:
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
        for key, item in self.cuisine.core.dir_paths.items():
            out += "mkdir -p %s\n" % item
        self.cuisine.core.execute_bash(out)

        self.cuisine.package.mdupdate()

        if not self.cuisine.core.isMac and not self.cuisine.core.isCygwin:
            self.cuisine.package.install("fuse")

        if self.cuisine.core.isArch:
            self.cuisine.package.install("wpa_actiond")  # is for wireless auto start capability
            self.cuisine.package.install("redis-server")

        self.cuisine.package.multiInstall(C)
        self.cuisine.package.upgrade()

        self.cuisine.package.clean()

        self.cuisine.bash.profileJS.addPath(j.sal.fs.joinPaths(self.cuisine.core.dir_paths["BASEDIR"], "bin"))
        self.cuisine.bash.profileJS.save()
