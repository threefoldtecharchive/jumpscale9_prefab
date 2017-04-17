
from JumpScale import j
from JumpScale.sal.fs.SystemFS import FileLock

base = j.tools.cuisine._getBaseClass()

LOCK_NAME = 'APT-LOCK'
LOCK_TIMEOUT = 500


class CuisinePackage(base):

    def _repository_ensure_apt(self, repository):
        self.ensure('python-software-properties')
        self.cuisine.core.sudo("add-apt-repository --yes " + repository)

    def _apt_get(self, cmd):
        CMD_APT_GET = 'DEBIAN_FRONTEND=noninteractive apt-get -q --yes -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" '
        cmd = CMD_APT_GET + cmd
        with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
            result = self.cuisine.core.sudo(cmd)
        # If the installation process was interrupted, we might get the following message
        # E: dpkg was interrupted, you must manually self.cuisine.core.run 'sudo
        # dpkg --configure -a' to correct the problem.
        if "sudo dpkg --configure -a" in result:
            with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
                self.cuisine.core.sudo("DEBIAN_FRONTEND=noninteractive dpkg --configure -a")
                result = self.cuisine.core.sudo(cmd)
        return result

    def update(self, package=None):
        if self.cuisine.core.isUbuntu:
            if package is None:
                return self._apt_get("-q --yes update")
            else:
                if type(package) in (list, tuple):
                    package = " ".join(package)
                return self._apt_get(' upgrade ' + package)
        elif self.cuisine.core.isAlpine:
            self.core.run("apk update")
            self.core.run("apk upgrade")
        else:
            raise j.exceptions.RuntimeError("could not install:%s, platform not supported" % package)

    def mdupdate(self):
        """
        update metadata of system
        """
        self.logger.info("packages mdupdate")
        if self._cuisine.core.isUbuntu:
            with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
                self.cuisine.core.run("apt-get update")
        elif self.cuisine.core.isAlpine:
            self.core.run("apk update")
        elif self.cuisine.core.isMac:
            location = self.cuisine.core.command_location("brew")
            # self.cuisine.core.run("sudo chown root %s" % location)
            self.cuisine.core.run("brew update")
        elif self.cuisine.core.isArch:
            self.cuisine.core.run("pacman -Syy")

    def upgrade(self, distupgrade=False):
        """
        upgrades system, distupgrade means ubuntu 14.04 will fo to e.g. 15.04
        """
        self.mdupdate()
        self.logger.info("packages upgrade")
        if self.cuisine.core.isUbuntu:
            if distupgrade:
                return self._apt_get("dist-upgrade")
            else:
                return self._apt_get("upgrade")
        elif self.cuisine.core.isArch:
            self.cuisine.core.run("pacman -Syu --noconfirm;pacman -Sc --noconfirm")
        elif self.cuisine.core.isMac:
            self.cuisine.core.run("brew upgrade")
        elif self.cuisine.core.isAlpine:
            self.core.run("apk update")
            self.core.run("apk upgrade")
        elif self.cuisine.core.isCygwin:
            return  # no such functionality in apt-cyg
        else:
            raise j.exceptions.RuntimeError("could not upgrade, platform not supported")

    def install(self, package, allow_unauthenticated=False, reset=False):

        self.logger.info("try to install:%s" % package)

        if self.doneGet("install_%s" % package) and reset == False:
            return

        if self.cuisine.core.isUbuntu:
            cmd = 'DEBIAN_FRONTEND=noninteractive apt-get -q --yes install '
            if allow_unauthenticated:
                cmd += ' --allow-unauthenticated '

            cmd += package

        elif self.cuisine.core.isAlpine:
            cmd = "apk add %s " % package

        elif self.cuisine.core.isArch:
            if package.startswith("python3"):
                package = "extra/python"

            # ignore
            for unsupported in ["libpython3.5-dev", "libffi-dev", "build-essential", "libpq-dev", "libsqlite3-dev"]:
                if unsupported in package:
                    package = 'devel'

            cmd = "pacman -S %s  --noconfirm" % package

        elif self.cuisine.core.isMac:
            for unsupported in ["libpython3.4-dev", "python3.4-dev", "libpython3.5-dev", "python3.5-dev",
                                "libffi-dev", "libssl-dev", "make", "build-essential", "libpq-dev", "libsqlite3-dev"]:
                if 'libsnappy-dev' in package or 'libsnappy1v5' in package:
                    package = 'snappy'

                if unsupported in package:
                    return

            _, installed, _ = self.cuisine.core.run("brew list", showout=False)
            if package in installed:
                self.logger.info("no need to install:%s" % package)
                return  # means was installed

            # rc,out=self.cuisine.core.run("brew info --json=v1 %s"%package,showout=False,die=False)
            # if rc==0:
            #     info=j.data.serializer.json.loads(out)
            #     return #means was installed

            if "wget" == package:
                package = "%s --enable-iri" % package

            cmd = "brew install %s " % package

        elif self.cuisine.core.isCygwin:
            if package in ["sudo", "net-tools"]:
                return

            installed = self.cuisine.core.run("apt-cyg list&")[1].splitlines()
            if package in installed:
                return  # means was installed

            cmd = "apt-cyg install %s&" % package
        else:
            raise j.exceptions.RuntimeError("could not install:%s, platform not supported" % package)

        mdupdate = False
        with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
            while True:
                rc, out, err = self.cuisine.core.run(cmd, die=False)

                if rc > 0:
                    if mdupdate is True:
                        raise j.exceptions.RuntimeError("Could not install:'%s' \n%s" % (package, out))

                    if out.find("not found") != -1 or out.find("failed to retrieve some files") != -1:
                        self.mdupdate()
                        mdupdate = True
                        continue
                    raise j.exceptions.RuntimeError("Could not install:%s %s" % (package, err))
                if rc == 0:
                    self.doneSet("install_%s" % package)
                    return out

    def multiInstall(self, packagelist, allow_unauthenticated=False):
        """
        @param packagelist is text file and each line is name of package
        can also be list

        e.g.
            # python
            mongodb

        @param runid, if specified actions will be used to execute
        """
        previous_sudo = self.cuisine.core.sudomode
        try:
            self.cuisine.core.sudomode = True

            if j.data.types.string.check(packagelist):
                packages = packagelist.strip().splitlines()
            elif j.data.types.list.check(packagelist):
                packages = packagelist
            else:
                raise j.exceptions.Input('packagelist should be string or a list. received a %s' % type(packagelist))

            to_install = []
            for dep in packages:
                dep = dep.strip()
                if dep is None or dep == "" or dep[0] == '#':
                    continue
                to_install.append(dep)

            for package in to_install:
                self.install(package, allow_unauthenticated=allow_unauthenticated)

        finally:
            self.cuisine.core.sudomode = previous_sudo

    def start(self, package):
        if self.cuisine.core.isArch or self.cuisine.core.isUbuntu or self.cuisine.core.isMac:
            self.cuisine.processmanager.ensure(package)
        else:
            raise j.exceptions.RuntimeError("could not install/ensure:%s, platform not supported" % package)

    def ensure(self, package, update=False):
        """Ensure apt packages are installed"""
        if self.cuisine.core.isUbuntu:
            if isinstance(package, str):
                package = package.split()
            res = {}
            for p in package:
                p = p.strip()
                if not p:
                    continue
                # The most reliable way to detect success is to use the command status
                # and suffix it with OK. This won't break with other locales.
                with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
                    _, status, _ = self.cuisine.core.run("dpkg-query -W -f='${Status} ' %s && echo **OK**;true" % p)
                if not status.endswith("OK") or "not-installed" in status:
                    self.install(p)
                    res[p] = False
                else:
                    if update:
                        self.update(p)
                    res[p] = True
            if len(res) == 1:
                for _, value in res.items():
                    return value
            else:
                return res
        elif self.cuisine.core.isArch:
            self.cuisine.core.run("pacman -S %s" % package)
            return
        elif self.cuisine.core.isMac:
            self.install(package)
            return
        else:
            raise j.exceptions.RuntimeError("could not install/ensure:%s, platform not supported" % package)

        raise j.exceptions.RuntimeError("not supported platform")

    def clean(self, package=None, agressive=False):
        """
        clean packaging system e.g. remove outdated packages & caching packages
        @param agressive if True will delete full cache

        """
        if self._cuisine.core.isUbuntu:
            with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
                if package is not None:
                    return self._apt_get("-y --purge remove %s" % package)
                else:
                    self.cuisine.core.run("apt-get autoremove -y")

            self._apt_get("autoclean")
            C = """
            apt-get clean
            rm -rf /bd_build
            rm -rf /tmp/* /var/tmp/*
            rm -f /etc/dpkg/dpkg.cfg.d/02apt-speedup

            find -regex '.*__pycache__.*' -delete
            rm -rf /var/log
            mkdir -p /var/log/apt
            rm -rf /var/tmp
            mkdir -p /var/tmp

            """
            self.cuisine.core.execute_bash(C)

        elif self.cuisine.core.isArch:
            cmd = "pacman -Sc"
            if agressive:
                cmd += "c"
            self.cuisine.core.run(cmd)
            if agressive:
                self.cuisine.core.run("pacman -Qdttq", showout=False)

        elif self.cuisine.core.isMac:
            if package:
                self.cuisine.core.run("brew cleanup %s" % package)
                self.cuisine.core.run("brew remove %s" % package)
            else:
                self.cuisine.core.run("brew cleanup")

        elif self.cuisine.core.isCygwin:
            if package:
                self.cuisine.core.run("apt-cyg remove %s" % package)
            else:
                pass

        else:
            raise j.exceptions.RuntimeError("could not package clean:%s, platform not supported" % package)

    def remove(self, package, autoclean=False):
        if self.cuisine.core.isUbuntu:
            self._apt_get('remove ' + package)
            if autoclean:
                self._apt_get("autoclean")
        elif self.isMac:
            self.cuisine.core.run("brew remove %s" % package)

    def __repr__(self):
        return "cuisine.package:%s:%s" % (self.executor.addr, self.executor.port)

    __str__ = __repr__
