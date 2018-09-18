
from Jumpscale import j
import time

base = j.tools.prefab._getBaseClass()

CMD_APT_GET = "DEBIAN_FRONTEND=noninteractive apt-get -q --yes -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' --allow-downgrades "


class PrefabPackage(base):

    def _repository_ensure_apt(self, repository):
        self.ensure('python-software-properties')
        self.prefab.core.run("add-apt-repository --yes " + repository)

    def _apt_wait_free(self):
        timeout = time.time() + 300
        while time.time() < timeout:
            _, out, _ = self.prefab.core.run(
                'fuser /var/lib/dpkg/lock', showout=False, die=False)
            if out.strip():
                time.sleep(1)
            else:
                return
        raise TimeoutError("resource dpkg is busy")

    def _apt_get(self, cmd):

        cmd = CMD_APT_GET + cmd
        result = self.prefab.core.run(cmd)
        # If the installation process was interrupted, we might get the following message
        # E: dpkg was interrupted, you must manually self.prefab.core.run 'run
        # dpkg --configure -a' to correct the problem.
        if "run dpkg --configure -a" in result:
            self.prefab.core.run(
                "DEBIAN_FRONTEND=noninteractive dpkg --configure -a")
            result = self.prefab.core.run(cmd)
        return result

    # def upgrade(self, package=None, reset=True):
    #     key = "upgrade_%s" % package
    #     if self.doneCheck(key, reset):
    #         return
    #     if self.prefab.core.isUbuntu:
    #         if package is None:
    #             return self._apt_get("-q --yes update")
    #         else:
    #             if type(package) in (list, tuple):
    #                 package = " ".join(package)
    #             return self._apt_get(' upgrade ' + package)
    #     elif self.prefab.core.isAlpine:
    #         self.core.run("apk update")
    #         self.core.run("apk upgrade")
    #     else:
    #         raise j.exceptions.RuntimeError(
    #             "could not install:%s, platform not supported" % package)
    #     self.doneSet(key)

    def mdupdate(self, reset=False):
        """
        update metadata of system
        """
        if self.doneCheck("mdupdate", reset):
            return
        self.logger.info("packages mdupdate")
        if self.prefab.core.isUbuntu:
            self.prefab.core.run("apt-get update")
        elif self.prefab.core.isAlpine:
            self.core.run("apk update")
        elif self.prefab.core.isMac:
            location = self.prefab.core.command_location("brew")
            # self.prefab.core.run("run chown root %s" % location)
            self.prefab.core.run("brew update")
        elif self.prefab.core.isArch:
            self.prefab.core.run("pacman -Syy")
        self.doneSet("mdupdate")

    def upgrade(self, distupgrade=False, reset=False):
        """
        upgrades system, distupgrade means ubuntu 14.04 will fo to e.g. 15.04
        """
        if self.doneCheck("upgrade", reset):
            return
        self.mdupdate()
        self.logger.info("packages upgrade")
        if self.prefab.core.isUbuntu:
            if distupgrade:
                raise NotImplementedError()
                # return self._apt_get("dist-upgrade")
            else:
                self._apt_get("upgrade -y")
        elif self.prefab.core.isArch:
            self.prefab.core.run(
                "pacman -Syu --noconfirm;pacman -Sc --noconfirm")
        elif self.prefab.core.isMac:
            self.prefab.core.run("brew upgrade")
        elif self.prefab.core.isAlpine:
            self.core.run("apk update")
            self.core.run("apk upgrade")
        elif self.prefab.core.isCygwin:
            return  # no such functionality in apt-cyg
        else:
            raise j.exceptions.RuntimeError(
                "could not upgrade, platform not supported")
        self.doneSet("upgrade")

    def install(self, package, reset=False):
        """
        """

        # bring to list of packages
        if j.data.types.list.check(package) == False and package.find(",") != -1:
            package = [item.strip() for item in package.split(",")]
        elif j.data.types.list.check(package) == False and package.find("\n") != -1:
            package = [item.strip() for item in package.split("\n")]
        elif not j.data.types.list.check(package):
            package = [package]

        packages = [item for item in package if item.strip() != ""]

        cmd = "set -ex\n"

        todo = []
        for package in packages:

            key = "install_%s" % package
            if self.doneCheck(key, reset):
                continue
            todo.append(package)
            print("+ install: %s" % package)

            self.logger.info("prepare to install:%s" % package)

            if self.prefab.core.isUbuntu:
                cmd += "%s install %s\n" % (CMD_APT_GET, package)

            elif self.prefab.core.isAlpine:
                cmd = "apk add %s \n" % package

            elif self.prefab.core.isArch:
                if package.startswith("python3"):
                    package = "extra/python"

                # ignore
                for unsupported in ["libpython3.5-dev", "libffi-dev", "build-essential", "libpq-dev", "libsqlite3-dev"]:
                    if unsupported in package:
                        package = 'devel'

                cmd = "pacman -S %s  --noconfirm\n" % package

            elif self.prefab.core.isMac:
                for unsupported in ["libpython3.4-dev", "python3.4-dev", "libpython3.5-dev", "python3.5-dev",
                                    "libffi-dev", "libssl-dev", "make", "build-essential", "libpq-dev", "libsqlite3-dev"]:
                    if 'libsnappy-dev' in package or 'libsnappy1v5' in package:
                        package = 'snappy'

                    if unsupported in package:
                        continue

                # rc,out=self.prefab.core.run("brew info --json=v1 %s"%package,showout=False,die=False)
                # if rc==0:
                #     info=j.data.serializers.json.loads(out)
                #     return #means was installed

                if "wget" == package:
                    package = "%s --enable-iri" % package

                cmd += "brew install %s || brew upgrade  %s\n" % (package, package)

            elif self.prefab.core.isCygwin:
                if package in ["run", "net-tools"]:
                    return

                installed = self.prefab.core.run(
                    "apt-cyg list&")[1].splitlines()
                if package in installed:
                    return  # means was installed

                cmd = "apt-cyg install %s\n" % package
            else:
                raise j.exceptions.RuntimeError(
                    "could not install:%s, platform not supported" % package)

            # mdupdate = False
            # while True:
            #     rc, out, err = self.prefab.core.run(cmd, die=False)

            #     if rc > 0:
            #         if mdupdate is True:
            #             raise j.exceptions.RuntimeError(
            #                 "Could not install:'%s' \n%s" % (package, out))

            #         if out.find("not found") != -1 or out.find("failed to retrieve some files") != -1:
            #             self.mdupdate()
            #             mdupdate = True
            #             continue
            #         raise j.exceptions.RuntimeError(
            #             "Could not install:%s %s" % (package, err))
            #     if rc == 0:
            #         self.doneSet(key)
            #         return out

        if len(todo) > 0:
            print(cmd)
            self.core.execute_bash(cmd)

        for package in todo:
            key = "install_%s," % package
            self.doneSet(key)

    # def multiInstall(self, packagelist, allow_unauthenticated=False, reset=False):
    #     """
    #     @param packagelist is text file and each line is name of package
    #     can also be list

    #     e.g.
    #         # python
    #         mongodb

    #     @param runid, if specified actions will be used to execute
    #     """
    #     # previous_run = self.prefab.core.runmode
    #     # try:
    #     #     self.prefab.core.runmode = True

    #     if j.data.types.string.check(packagelist):
    #         packages = packagelist.strip().splitlines()
    #     elif j.data.types.list.check(packagelist):
    #         packages = packagelist
    #     else:
    #         raise j.exceptions.Input(
    #             'packagelist should be string or a list. received a %s' % type(packagelist))

    #     to_install = []
    #     for dep in packages:
    #         dep = dep.strip()
    #         if dep is None or dep == "" or dep[0] == '#':
    #             continue
    #         to_install.append(dep)

    #     for package in to_install:
    #         self.install(
    #             package, allow_unauthenticated=allow_unauthenticated, reset=reset)

    def start(self, package):
        if self.prefab.core.isArch or self.prefab.core.isUbuntu or self.prefab.core.isMac:
            pm = self.prefab.system.processmanager.get()
            pm.ensure(package)
        else:
            raise j.exceptions.RuntimeError(
                "could not install/ensure:%s, platform not supported" % package)

    def ensure(self, package, update=False):
        """Ensure apt packages are installed"""
        if self.prefab.core.isUbuntu:
            if isinstance(package, str):
                package = package.split()
            res = {}
            for p in package:
                p = p.strip()
                if not p:
                    continue
                # The most reliable way to detect success is to use the command status
                # and suffix it with OK. This won't break with other locales.
                rc, out, err = self.prefab.core.run(
                    "dpkg -s %s && echo **OK**;true" % p)
                if "is not installed" in err:
                    self.install(p)
                    res[p] = False
                else:
                    if update:
                        self.mdupdate(p)
                    res[p] = True
            if len(res) == 1:
                for _, value in res.items():
                    return value
            else:
                return res
        elif self.prefab.core.isArch:
            self.prefab.core.run("pacman -S %s" % package)
            return
        elif self.prefab.core.isMac:
            self.install(package)
            return
        else:
            raise j.exceptions.RuntimeError(
                "could not install/ensure:%s, platform not supported" % package)

        raise j.exceptions.RuntimeError("not supported platform")

    def clean(self, package=None, agressive=False):
        """
        clean packaging system e.g. remove outdated packages & caching packages
        @param agressive if True will delete full cache

        """
        if self.prefab.core.isUbuntu:

            if package is not None:
                return self._apt_get("-y --purge remove %s" % package)
            else:
                self.prefab.core.run("apt-get autoremove -y")

            self._apt_get("autoclean")
            C = """
            apt-get clean
            rm -rf /bd_build
            rm -rf /var/tmp/*
            rm -f /etc/dpkg/dpkg.cfg.d/02apt-speedup

            find -regex '.*__pycache__.*' -delete
            rm -rf /var/log
            mkdir -p /var/log/apt
            rm -rf /var/tmp
            mkdir -p /var/tmp

            """
            self.prefab.core.execute_bash(C)

        elif self.prefab.core.isArch:
            cmd = "pacman -Sc"
            if agressive:
                cmd += "c"
            self.prefab.core.run(cmd)
            if agressive:
                self.prefab.core.run("pacman -Qdttq", showout=False)

        elif self.prefab.core.isMac:
            if package:
                self.prefab.core.run("brew cleanup %s" % package)
                self.prefab.core.run("brew remove %s" % package)
            else:
                self.prefab.core.run("brew cleanup")

        elif self.prefab.core.isCygwin:
            if package:
                self.prefab.core.run("apt-cyg remove %s" % package)
            else:
                pass

        else:
            raise j.exceptions.RuntimeError(
                "could not package clean:%s, platform not supported" % package)

    def remove(self, package, autoclean=False):
        if self.prefab.core.isUbuntu:
            self._apt_get('remove ' + package)
            if autoclean:
                self._apt_get("autoclean")
        elif self.prefab.core.isMac:
            self.prefab.core.run("brew remove %s 2>&1 > /dev/null|echo """ % package)

    def __repr__(self):
        return "prefab.system.package:%s:%s" % (self.executor.addr, self.executor.port)

    __str__ = __repr__
