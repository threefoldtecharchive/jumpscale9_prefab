
from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineJS8_G8OS(base):

    def jumpscale_installed(self, die=False):
        rc1, out1, err = self.cuisine.core.run('which js8', die=False)
        rc2, out2, err = self.cuisine.core.run('which js', die=False)
        if (rc1 == 0 and out1) or (rc2 == 0 and out2):
            return True
        return False

    def jumpscale9(self, rw=False, reset=False):
        """
        install jumpscale, will be done as sandbox

        @param rw if True install sandbox in RW mode
        @param reset, remove old code (only used when rw mode)

        """
        import time
        if self.jumpscale_installed() and not reset:
            return
        self.base()

        C = """
            js8 stop
            set -ex
            cd /usr/bin
            rm -f js8
            cd /usr/local/bin
            rm -f js8
            rm -f /usr/local/bin/jspython
            rm -f /usr/local/bin/js
            rm -fr /opt/*
            """
        self.cuisine.core.execute_bash(C)

        if not self.cuisine.core.isUbuntu:
            raise j.exceptions.RuntimeError("not supported yet")

        if reset:
            C = """
                set +ex
                rm -rf /opt
                rm -rf /optrw
                """
            self.cuisine.core.execute_bash(C)

        C = """
            wget https://stor.jumpscale.org/storx/static/js8 -O /usr/local/bin/js8
            chmod +x /usr/local/bin/js8
            cd /
            mkdir -p $BASEDIR
            """
        self.cuisine.core.execute_bash(C)

        """
        install jumpscale9 sandbox in read or readwrite mode
        """
        C = """
            set -ex
            rm -rf /opt
            cd /usr/local/bin
            """
        if rw:
            C += "./js8 -rw init"
        else:
            C += "./js8 init"
        self.cuisine.core.execute_bash(C)

        start = j.data.time.epoch
        timeout = 30
        while start + timeout > j.data.time.epoch:
            if not self.cuisine.core.file_exists('/opt/jumpscale9/bin/jspython'):
                time.sleep(2)
            else:
                self.cuisine.core.file_link('/opt/jumpscale9/bin/jspython', '/usr/local/bin/jspython')
                self.cuisine.core.file_link('/opt/jumpscale9/bin/js', '/usr/local/bin/js')
                self.cuisine.bash.include('/opt/jumpscale9/env.sh')
                break

        self.logger.info("* re-login into your shell to have access to js, because otherwise the env arguments are not set properly.")

    def base(self):
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
