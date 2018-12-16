from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabGeoDns(app):
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
        # self.prefab.runtimes.golang.install(force=False)
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install(["libgeoip-dev", 'build-essential', 'pkg-config'])

        # build
        self.prefab.runtimes.golang.get("github.com/abh/geodns")

        # moving files and creating config
        self.prefab.core.dir_ensure('{DIR_BIN}')
        self.prefab.core.file_copy("{DIR_BASE}/go/bin/geodns", "{DIR_BIN}")
        self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/geodns/dns", recursive=True)
        profile = self.prefab.bash.profileDefault
        profile.addPath('{DIR_BIN}')
        profile.save()

        self.prefab.core.file_copy(
            "$TEMPLATEDIR/cfg/geodns", "{DIR_BASE}/cfg/", recursive=True)

    def start(self, ip="0.0.0.0", port="5053", config_dir="{DIR_BASE}/cfg/geodns/dns/",
              identifier="geodns_main", cpus="1", tmux=False):
        """
        starts geodns server with given params
        """
        if self.prefab.core.dir_exists(config_dir):
            self.prefab.core.dir_ensure(config_dir)
        cmd = "{DIR_BIN}/geodns -interface %s -port %s -config=%s -identifier=%s -cpus=%s" % (
            ip, str(port), config_dir, identifier, str(cpus))
        if tmux:
            pm = self.prefab.system.processmanager.get("tmux")
            pm.ensure(name=identifier, cmd=cmd, env={}, path="{DIR_BIN}")
        else:
            pm = self.prefab.system.processmanager.get()
            pm.ensure(name=identifier, cmd=cmd, env={}, path="{DIR_BIN}")

    def stop(self, name="geodns_main"):
        """
        stop geodns server with @name
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop(name)
