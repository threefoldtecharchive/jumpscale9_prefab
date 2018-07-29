from jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabTraefik(app):
    NAME = "traefik"

    def _init(self):
        self.BUILDDIR_ = self.replace("$BUILDDIR/traefik")

    def reset(self):
        self.stop()
        app.reset(self)
        self._init()
        self.prefab.core.dir_remove(self.BUILDDIR_)
        self.prefab.core.dir_remove("$BINDIR/traefik")

    def install(self, plugins=None, reset=False, configpath="{{CFGDIR}}/traefik.cfg"):
        """
        will build if required & then install binary on right location
        """

        raise RuntimeError("not implemented yet, now copy from caddy")

        if self.doneGet('install') and reset is False and self.isInstalled():
            return

        self.prefab.bash.profileDefault.addPath(self.prefab.core.dir_paths['BINDIR'])
        self.prefab.bash.profileDefault.save()

        configpath = self.replace(configpath)

        if not self.prefab.core.exists(configpath):
            # default configuration, can overwrite
            self.configure(configpath=configpath)

        port = self.getTCPPort(configpath=configpath)

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
                  logdir="{{LOGDIR}}/caddy/log", email='info@greenitglobe.com', port=8000):
        """
        @param caddyconfigfile
            template args available DATADIR, LOGDIR, WWWROOTDIR, PORT, TMPDIR, EMAIL ... (using mustasche)
        """

        C = """
        #tcpport:{{PORT}}
        :{{PORT}}
        gzip
        log {{LOGDIR}}/access.log
        errors {
            * {{LOGDIR}}/errors.log
        }
        root {{WWWROOTDIR}}
        """

        configpath = self.replace(configpath)

        args = {}
        args["WWWROOTDIR"] = self.replace(wwwrootdir).rstrip("/")
        args["LOGDIR"] = self.replace(logdir).rstrip("/")
        args["PORT"] = str(port)
        args["EMAIL"] = email
        args["CONFIGPATH"] = configpath

        C = self.replace(C, args)

        self.prefab.core.dir_ensure(args["LOGDIR"])
        self.prefab.core.dir_ensure(args["WWWROOTDIR"])

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

        if not j.sal.fs.exists(configpath, followlinks=True):
            raise RuntimeError(
                "could not find caddyconfigfile:%s" % configpath)

        tcpport = int(self.getTCPPort(configpath=configpath))

        # TODO: *1 reload does not work yet
        # if self.reload(configpath=configpath) == True:
        #     self.logger.info("caddy already started, will reload")
        #     return
        pm = self.prefab.system.processmanager.get()
        pm.stop("caddy")  # will also kill

        cmd = self.prefab.bash.cmdGetPath("caddy")
        if agree:
            agree = " -agree"

        print (cmd)

        # self.prefab.system.processmanager.ensure(
        #     "caddy", 'ulimit -n 8192; %s -conf=%s -email=%s %s' % (cmd, args["CONFIGPATH"], args["EMAIL"], agree), wait=1)
        pm.ensure(
            "caddy", 'ulimit -n 8192; %s -conf=%s %s' % (cmd, configpath, agree), wait=1, expect=expect)

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("caddy")
