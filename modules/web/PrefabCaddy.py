from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabCaddy(app):
    NAME = "caddy"

    def _init(self):
        self.BUILDDIR_ = self.replace("$BUILDDIR/caddy")

    def reset(self):
        self.stop()
        app.reset(self)
        self._init()
        self.prefab.core.dir_remove(self.BUILDDIR_)
        self.prefab.core.dir_remove("$BINDIR/caddy")

    def build(self, reset=False, plugins=None):
        """
        Get/Build the binaries of caddy itself.
        :param reset: boolean to reset the build process
        :param plugins: list of plugins names to be installed
        :return:
        """
        # if not self.core.isUbuntu:
        #     raise j.exceptions.RuntimeError("only ubuntu supported")

        if self.doneCheck('build', reset):
            return

        self.prefab.system.base.install(upgrade=True)
        golang = self.prefab.runtimes.golang
        golang.install()

        # build caddy from source using our caddyman
        self.prefab.tools.git.pullRepo("https://github.com/incubaid/caddyman", dest="/tmp/caddyman")
        self.prefab.core.run("cd /tmp/caddyman && chmod u+x caddyman.sh")
        if not plugins:
            plugins = ["iyo"]
        cmd = "/tmp/caddyman/caddyman.sh install {plugins}".format(plugins=" ".join(plugins))
        self.prefab.core.run(cmd)
        self.doneSet('build')

    def install(self, plugins=None, reset=False, configpath="{{CFGDIR}}/caddy.cfg"):
        """
        will build if required & then install binary on right location
        """
        self.build(plugins=plugins, reset=reset)

        if self.doneCheck('install', reset):
            return

        self.prefab.core.file_copy('/opt/go_proj/bin/caddy', '$BINDIR/caddy')
        self.prefab.bash.profileDefault.addPath(self.prefab.core.dir_paths['BINDIR'])
        self.prefab.bash.profileDefault.save()

        configpath = self.replace(configpath)

        if not self.prefab.core.exists(configpath):
            # default configuration, can overwrite
            self.configure(configpath=configpath)

        fw = not self.prefab.core.run("ufw status 2> /dev/null", die=False)[0]

        port = self.getTCPPort(configpath=configpath)

        # Do if not  "ufw status 2> /dev/null" didn't run properly
        if fw:
            self.prefab.security.ufw.allowIncoming(port)

        if self.prefab.system.process.tcpport_check(port, ""):
            raise RuntimeError(
                "port %s is occupied, cannot install caddy" % port)

        self.doneSet('install')

    def reload(self, configpath="{{CFGDIR}}/caddy.cfg"):
        configpath = self.replace(configpath)
        for item in self.prefab.system.process.info_get():
            if item["process"] == "caddy":
                pid = item["pid"]
                self.prefab.core.run("kill -s USR1 %s" % pid)
                return True
        return False

    def configure(self, ssl=False, wwwrootdir="{{DATADIR}}/www/", configpath="{{CFGDIR}}/caddy.cfg",
                  logdir="{{LOGDIR}}/caddy/log", email='replaceme', port=8000):
        """
        @param caddyconfigfile
            template args available DATADIR, LOGDIR, WWWROOTDIR, PORT, TMPDIR, EMAIL ... (using mustasche)
        """
        vhosts_dir = self.replace("{{CFGDIR}}/vhosts")
        self.prefab.core.dir_ensure(vhosts_dir)
        C = """
        #tcpport:{{PORT}}
        import {{VHOSTS_DIR}}/*
        """

        configpath = self.replace(configpath)
        args = {
            "PORT": str(port),
            "VHOSTS_DIR": vhosts_dir
        }
        C = self.replace(C, args)
        self.prefab.core.file_write(configpath, C)

    def getTCPPort(self, configpath="{{CFGDIR}}/caddy.cfg"):
        configpath = self.replace(configpath)
        C = self.prefab.core.file_read(configpath)
        for line in C.split("\n"):
            if "#tcpport:" in line:
                return line.split(":")[1].strip()
        raise RuntimeError(
            "Can not find tcpport arg in config file, needs to be '#tcpport:'")

    def start(self, configpath="{{CFGDIR}}/caddy.cfg", agree=True, expect="done."):
        """
        @expect is to see if we can find this string in output of caddy starting
        """

        configpath = self.replace(configpath)

        if not self.prefab.core.exists(configpath):
            raise RuntimeError(
                "could not find caddyconfigfile:%s" % configpath)

        # tcpport = int(self.getTCPPort(configpath=configpath))

        # TODO: *1 reload does not work yet
        # if self.reload(configpath=configpath) == True:
        #     self.logger.info("caddy already started, will reload")
        #     return

        self.stop()  # will also kill

        if self.prefab.platformtype.isMac:
            cmd = "caddy"
        else:
            cmd = self.replace("$BINDIR/caddy")

        if agree:
            agree = " -agree"

        cmd = 'ulimit -n 8192; %s -conf=%s %s' % (cmd, configpath, agree)
        # wait 10 seconds for caddy to generate ssl certificate before returning error
        self.prefab.system.processmanager.get().ensure("caddy", cmd, wait=10, expect=expect)

    def stop(self):
        self.prefab.system.processmanager.get().stop("caddy")

    def add_website(self, name, cfg, configpath="{{CFGDIR}}/caddy.cfg"):
        file_contents = self.prefab.core.file_read(configpath)
        vhosts_dir = self.replace("{{CFGDIR}}/vhosts")
        if vhosts_dir not in file_contents:
            file_contents = "import {}/*\n".format(vhosts_dir) + file_contents
        self.prefab.core.file_write(configpath, file_contents)
        self.prefab.core.dir_ensure(vhosts_dir)
        cfg_path = "{}/{}.conf".format(vhosts_dir, name)
        self.prefab.core.file_write(cfg_path, cfg)
        self.stop()
        self.start()
