from js9 import j


app = j.tools.prefab._getBaseAppClass()
import pystache


class PrefabCaddy(app):

    NAME = "caddy"
    defaultplugins = ['http.filemanager', 'http.cors']

    def _init(self):
        self.BUILDDIR_ = self.replace("$BUILDDIR/caddy")
        self.CODEDIR_ = self.replace("$CODEDIR/github/mholt/caddy")

    def reset(self):
        app.reset(self)
        self._init()

    def build(
            self,
            reset=False,
            plugins=defaultplugins):
        """
        Get/Build the binaries of caddy itself.
        :param plugins: is used to specify the required plugins in the installation. Currently the default installation
        will add the following plugins: filemanager, cors
        """
        if self.doneGet('build') and reset is False:
            return

        plugins = ",".join(plugins)
        if self.core.isMac:
            caddy_url = 'https://caddyserver.com/download/darwin/amd64?plugins=%s' % plugins
            dest = '$TMPDIR/caddy_darwin_amd64_custom.zip'
        else:
            caddy_url = 'https://caddyserver.com/download/linux/amd64?plugins=%s' % plugins
            dest = '$TMPDIR/caddy_linux_amd64_custom.tar.gz'
        self.prefab.core.file_download(caddy_url, dest)
        self.prefab.core.run('cd $TMPDIR && tar xvf %s' % dest)
        self.doneSet('build')

    def install(self, plugins=defaultplugins, reset=False, configpath="{{CFGDIR}}/caddy.cfg"):
        """
        will build if required & then install binary on right location
        """

        if not self.doneGet('build'):
            self.build(plugins=plugins)

        if self.doneGet('install') and reset is False and self.isInstalled():
            return

        self.prefab.core.dir_paths_create()

        self.prefab.core.file_copy(
            '$TMPDIR/caddy', '$BINDIR/caddy')

        self.prefab.bash.profileDefault.addPath(self.prefab.core.dir_paths['BINDIR'])
        self.prefab.bash.profileDefault.save()

        configpath = self.replace(configpath)

        if not self.prefab.core.exists(configpath):
            self.configure(configpath=configpath)  # default configuration, can overwrite

        fw = not self.prefab.core.run("ufw status 2> /dev/null", die=False)[0]

        port = self.getTCPPort(configpath=configpath)

        # Do if not  "ufw status 2> /dev/null" didn't run properly
        if fw:
            self.prefab.systemservices.ufw.allowIncoming(port)

        if self.prefab.process.tcpport_check(port, ""):
            raise RuntimeError("port %s is occupied, cannot install caddy" % port)

        self.doneSet('install')

    def reload(self, configpath="{{CFGDIR}}/caddy.cfg"):
        configpath = self.replace(configpath)
        for item in self.prefab.process.info_get():
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
        # errors {
        #     log {{LOGDIR}}/errors.log
        # }
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
        raise RuntimeError("Can not find tcpport arg in config file, needs to be '#tcpport:'")

    def start(self, configpath="{{CFGDIR}}/caddy.cfg", agree=True, expect="done."):
        """
        @expect is to see if we can find this string in output of caddy starting
        """

        configpath = self.replace(configpath)

        self.install()

        if not j.sal.fs.exists(configpath, followlinks=True):
            raise RuntimeError("could not find caddyconfigfile:%s" % configpath)

        tcpport = int(self.getTCPPort(configpath=configpath))

        # TODO: *1 reload does not work yet
        # if self.reload(configpath=configpath) == True:
        #     self.logger.info("caddy already started, will reload")
        #     return

        self.prefab.processmanager.stop("caddy")  # will also kill

        cmd = self.prefab.bash.cmdGetPath("caddy")
        if agree:
            agree = " -agree"

        # self.prefab.processmanager.ensure(
        #     "caddy", 'ulimit -n 8192; %s -conf=%s -email=%s %s' % (cmd, args["CONFIGPATH"], args["EMAIL"], agree), wait=1)
        self.prefab.processmanager.ensure(
            "caddy", 'ulimit -n 8192; %s -conf=%s %s' % (cmd, configpath, agree), wait=1, expect=expect)

    def stop(self):
        self.prefab.processmanager.stop("caddy")
