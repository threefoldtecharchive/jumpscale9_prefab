from js9 import j


app = j.tools.cuisine._getBaseAppClass()


class CuisineGeoDns(app):
    NAME = "geodns"

    def reset(self):
        app.reset(self)
        self._init()

    def install(self, reset=False):
        """
        installs and builds geodns from github.com/abh/geodns
        """
        if reset is False and self.isInstalled():
            return
        # deps
        # self.cuisine.development.golang.install(force=False)
        self.cuisine.package.mdupdate()
        self.cuisine.package.multiInstall(["libgeoip-dev", 'build-essential', 'pkg-config'])

        # build
        self.cuisine.development.golang.get("github.com/abh/geodns")

        # moving files and creating config
        self.cuisine.core.dir_ensure('$BINDIR')
        self.cuisine.core.file_copy("$GOPATHDIR/bin/geodns", "$BINDIR")
        self.cuisine.core.dir_ensure("$TEMPLATEDIR/cfg/geodns/dns", recursive=True)
        profile = self.cuisine.bash.profileDefault
        profile.addPath('$BINDIR')
        profile.save()

        self.cuisine.core.file_copy(
            "$TEMPLATEDIR/cfg/geodns", "$JSCFGDIR/", recursive=True)

    def start(self, ip="0.0.0.0", port="5053", config_dir="$JSCFGDIR/geodns/dns/",
              identifier="geodns_main", cpus="1", tmux=False):
        """
        starts geodns server with given params
        """
        if self.cuisine.core.dir_exists(config_dir):
            self.cuisine.core.dir_ensure(config_dir)
        cmd = "$BINDIR/geodns -interface %s -port %s -config=%s -identifier=%s -cpus=%s" % (
            ip, str(port), config_dir, identifier, str(cpus))
        if tmux:
            pm = self.cuisine.processmanager.get("tmux")
            pm.ensure(name=identifier, cmd=cmd, env={}, path="$BINDIR")
        else:
            self.cuisine.processmanager.ensure(name=identifier, cmd=cmd, env={}, path="$BINDIR")

    def stop(self, name="geodns_main"):
        """
        stop geodns server with @name
        """
        self.cuisine.processmanager.stop(name)
