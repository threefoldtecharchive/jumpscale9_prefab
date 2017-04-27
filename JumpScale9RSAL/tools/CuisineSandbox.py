

from js9 import j

base = j.tools.cuisine._getBaseClass()


class CuisineSandbox(base):

    def do(self, destination="/out", reset=False):
        """
        TODO: specify what comes in /out

        """
        self.cuisine.development.js8.install()
        self.cuisine.package.mdupdate()

        self.cuisine.core.file_copy('/usr/local/bin/jspython', '$BINDIR')

        sandbox_script = """
        cuisine = j.tools.cuisine.local
        cuisine.apps.brotli.build()
        cuisine.apps.brotli.install()
        paths = []
        paths.append("/usr/lib/python3/dist-packages")
        paths.append("/usr/lib/python3.5/")
        paths.append("/usr/local/lib/python3.5/dist-packages")

        excludeFileRegex=["-tk/", "/lib2to3", "-34m-", ".egg-info","lsb_release"]
        excludeDirRegex=["/JumpScale", "\.dist-info", "config-x86_64-linux-gnu", "pygtk"]

        dest = j.sal.fs.joinPaths(cuisine.core.dir_paths['base'], 'lib')

        for path in paths:
            j.tools.sandboxer.copyTo(path, dest, excludeFileRegex=excludeFileRegex, excludeDirRegex=excludeDirRegex)

        base=cuisine.core.dir_paths['base']

        if not j.sal.fs.exists("%s/bin/python" % base):
            j.sal.fs.symlink("%s/bin/python3" % base,"%s/bin/python3.5" % base)

        j.tools.sandboxer.sandboxLibs("%s/lib" % base, recursive=True)
        j.tools.sandboxer.sandboxLibs("%s/bin" % base, recursive=True)
        """
        self.logger.info("start sandboxing")
        self.cuisine.core.execute_jumpscript(sandbox_script)

        name = "js8"

        if reset:
            self.logger.info("remove previous build info")
            self.core.dir_remove("%s/%s" % (destination, name))

        self.core.dir_remove("%s/%s/" % (destination, name))

        dedupe_script = """
        j.tools.sandboxer.dedupe('/opt', storpath='$out/$name', name='js8_opt', reset=False, append=True, excludeDirs=['/opt/code'])
        """
        dedupe_script = dedupe_script.replace("$name", name)
        dedupe_script = dedupe_script.replace("$out", destination)
        self.logger.info("start dedupe")
        self.cuisine.core.execute_jumpscript(dedupe_script)

        copy_script = """
        j.sal.fs.removeDirTree("$out/$name/jumpscale9/")
        j.sal.fs.copyDirTree("/opt/jumpscale9/","$out/$name/jumpscale9",deletefirst=True,ignoredir=['.egg-info', '.dist-info','__pycache__'],ignorefiles=['.egg-info',"*.pyc"])
        j.sal.fs.removeIrrelevantFiles("$out")
        """
        copy_script = copy_script.replace("$name", name)
        copy_script = copy_script.replace("$out", destination)
        self.logger.info("start copy sandbox")
        self.cuisine.core.execute_jumpscript(copy_script)

    def cleanup(self, aggressive=False):
        self.cuisine.core.run("apt-get clean")
        self.cuisine.core.dir_remove("/var/tmp/*")
        self.cuisine.core.dir_remove("/etc/dpkg/dpkg.cfg.d/02apt-speedup")
        self.cuisine.core.dir_remove("$TMPDIR")
        self.cuisine.core.dir_ensure("$TMPDIR")

        self.cuisine.core.dir_remove("$GOPATHDIR/src/*")
        self.cuisine.core.dir_remove("$TMPDIR/*")
        self.cuisine.core.dir_remove("$VARDIR/data/*")
        self.cuisine.core.dir_remove('/opt/code/github/domsj', True)
        self.cuisine.core.dir_remove('/opt/code/github/openvstorage', True)

        C = """
        cd /opt;find . -name '*.pyc' -delete
        cd /opt;find . -name '*.log' -delete
        cd /opt;find . -name '__pycache__' -delete
        """
        self.cuisine.core.execute_bash(C)

        if aggressive:
            C = """
            set -ex
            cd /
            find -regex '.*__pycache__.*' -delete
            rm -rf /var/log
            mkdir -p /var/log/apt
            rm -rf /var/tmp
            mkdir -p /var/tmp
            rm -rf /usr/share/doc
            mkdir -p /usr/share/doc
            rm -rf /usr/share/gcc-5
            rm -rf /usr/share/gdb
            rm -rf /usr/share/gitweb
            rm -rf /usr/share/info
            rm -rf /usr/share/lintian
            rm -rf /usr/share/perl
            rm -rf /usr/share/perl5
            rm -rf /usr/share/pyshared
            rm -rf /usr/share/python*
            rm -rf /usr/share/zsh

            rm -rf /usr/share/locale-langpack/en_AU
            rm -rf /usr/share/locale-langpack/en_CA
            rm -rf /usr/share/locale-langpack/en_GB
            rm -rf /usr/share/man

            rm -rf /usr/lib/python*
            rm -rf /usr/lib/valgrind

            rm -rf /usr/bin/python*
            """
            self.cuisine.core.execute_bash(C)

        self.cuisine.core.dir_ensure(self.cuisine.core.dir_paths["TMPDIR"])
        if not self.cuisine.core.isMac and not self.cuisine.core.isCygwin:
            C = """
                set +ex
                # pkill redis-server #will now kill too many redis'es, should only kill the one not in docker
                # pkill redis #will now kill too many redis'es, should only kill the one not in docker
                umount -fl /optrw
                apt-get remove redis-server -y
                rm -rf /overlay/js_upper
                rm -rf /overlay/js_work
                rm -rf /optrw
                js8 stop
                pkill js8
                umount -f /opt
                echo "OK"
                """
        if self.cuisine.core.isMac:
            C = """
                set +ex
                js8 stop
                pkill js8
                echo "OK"
                """
        if self.cuisine.core.isCygwin:
            C = """
                set +ex
                js8 stop
                pskill js8
                echo "OK"
                """

        self.cuisine.core.execute_bash(C)
