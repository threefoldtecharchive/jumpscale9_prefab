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
        self.stop()
        app.reset(self)
        self._init()
        self.prefab.core.dir_remove(self.BUILDDIR_)
        self.prefab.core.dir_remove("$BINDIR/caddy")


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

    def install(self, plugins=defaultplugins, reset=False):
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

        self.doneSet('install')

    def start(self, ssl=False, wwwrootdir="{{DATADIR}}/www/", configpath="{{CFGDIR}}/caddy.cfg",
              logdir="{{LOGDIR}}/caddy/log", agree=True, email='info@greenitglobe.com', port=8000,
              caddyconfigfile="", plugins=defaultplugins):
        """
        @param caddyconfigfile
            template args available DATADIR, LOGDIR, WWWROOTDIR, PORT, TMPDIR, EMAIL ... (using mustasche)
        """
        self.install(plugins=plugins)

        C = """
        :{{PORT}}
        gzip
        log {{LOGDIR}}/access.log
        # errors {
        #     log {{LOGDIR}}/errors.log
        # }
        root {{WWWROOTDIR}}
        """

        args = {}
        args["WWWROOTDIR"] = self.replace(wwwrootdir).rstrip("/")
        args["LOGDIR"] = self.replace(logdir).rstrip("/")
        args["PORT"] = str(port)
        args["EMAIL"] = email
        args["CONFIGPATH"] = self.replace(configpath)

        C = self.replace(C, args)

        self.prefab.core.dir_ensure(args["LOGDIR"])
        self.prefab.core.dir_ensure(args["WWWROOTDIR"])

        self.prefab.core.file_write(configpath, C)

        self.prefab.processmanager.stop("caddy")  # will also kill

        fw = not self.prefab.core.run("ufw status 2> /dev/null", die=False)[0]

        # Do if not  "ufw status 2> /dev/null" didn't run properly
        if fw:
            self.prefab.systemservices.ufw.allowIncoming(port)

        if self.prefab.process.tcpport_check(port, ""):
            raise RuntimeError("port %s is occupied, cannot install caddy" % port)

        cmd = self.prefab.bash.cmdGetPath("caddy")
        if agree:
            agree = " -agree"

        self.prefab.processmanager.ensure(
            "caddy", 'ulimit -n 8192; %s -conf=%s -email=%s %s' % (cmd, args["CONFIGPATH"], args["EMAIL"], agree), wait=1)

    def stop(self):
        self.prefab.processmanager.stop("caddy")
