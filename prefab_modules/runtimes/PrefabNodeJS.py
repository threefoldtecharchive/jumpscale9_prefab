from Jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabNodeJS(app):
    NAME = 'nodejs'

    def _init(self):
        self._bowerDir = ""

    @property
    def npm(self):
        return self.executor.replace('{DIR_BASE}/node/bin/npm')

    @property
    def NODE_PATH(self):
        return self.executor.replace('{DIR_BASE}/node/lib/node_modules')

    def bowerInstall(self, name):
        """
        @param name can be a list or string
        """
        if self._bowerDir == "":
            self.install()
            self.prefab.core.dir_ensure("{DIR_TEMP}/bower")
            self._bowerDir = self.executor.replace("{DIR_TEMP}/bower")
        if j.data.types.list.check(name):
            for item in name:
                self.bowerInstall(item)
        else:
            self.logger.info("bower install %s" % name)
            self.prefab.core.run(
                "cd %s;bower --allow-root install  %s" % (self._bowerDir, name), profile=True)

    def isInstalled(self):
        rc, out, err = self.prefab.core.run(
            "npm version", die=False, showout=False)
        if rc > 0:
            return False
        installedDict = j.data.serializers.yaml.loads(out)
        if "npm" not in installedDict or "node" not in installedDict:
            return False
        if j.core.text.strToVersionInt(installedDict["npm"]) < 5000000:
            self.logger.info("npm too low version, need to install.")
            return False
        if j.core.text.strToVersionInt(installedDict["node"]) < 7000000:
            self.logger.info("node too low version, need to install.")
            return False

        if self.doneGet("install") is False:
            return False
        return True

    def phantomjs(self, reset=False):
        """
        headless browser used for automation
        """
        if self.doneGet("phantomjs") and reset is False:
            return
        if self.prefab.core.isUbuntu:

            url = 'https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2'
            cdest = self.prefab.core.file_download(
                url, expand=True, overwrite=False, to="{DIR_TEMP}/phantomjs", removeTopDir=True, deletedest=True)

            self.core.run("mv %s/bin/phantomjs /opt/bin/phantomjs" % cdest)
            self.core.run("rm -rf %s" % cdest)

            self.prefab.system.package.install("libfontconfig")

        elif self.prefab.core.isMac:
            self.prefab.system.package.install("phantomjs")

        else:
            raise RuntimeError("phantomjs only supported don ubuntu or osx")

        self.doneSet("phantomjs")

    def npm_install(self, name, global_=True, reset=False):
        """
        @PARAM cmdname is the optional cmd name which will be used to put in path of the env (as alias to the name)
        """
        self.logger.info("npm install:%s" % name)
        key = "npm_%s" % name
        if self.doneGet(key) and not reset:
            return

        if global_:
            if self.prefab.core.isMac:
                sudo = "sudo "
            else:
                sudo = ""
            cmd = "cd /tmp;%snpm install -g %s --unsafe-perm=true --allow-root" % (sudo, name)
        else:
            cmd = "cd %s;npm i %s" % (self.NODE_PATH, name)

        self.prefab.core.run(cmd)

        # cmdpath = "%s/nodejs_modules/node_modules/%s/bin/%s" % (
        #     j.dirs.VARDIR, name, name)

        # from IPython import embed
        # embed(colors='Linux')

        # if j.sal.fs.exists(srcCmd):
        #     j.sal.fs.chmod(srcCmd, 0o770)
        #     j.sal.fs.symlink(srcCmd, "/usr/local/bin/%s" %
        #                      name, overwriteTarget=True)
        #     j.sal.fs.chmod(srcCmd, 0o770)

        # if j.sal.fs.exists(cmdpath):
        #     j.sal.fs.symlink(cmdpath, "/usr/local/bin/%s" %
        #                      name, overwriteTarget=True)

        self.doneSet(key)

    def install(self, reset=False):
        """
        """
        if self.isInstalled() and not reset:
            return

        self.prefab.core.file_unlink("{DIR_BIN}/node")
        self.prefab.core.dir_remove("{DIR_BASE}/apps/npm")

        # version = "7.7.1"
        version = "8.4.0"

        if reset is False and self.prefab.core.file_exists('{DIR_BIN}/npm'):
            return

        if self.prefab.core.isMac:
            url = 'https://nodejs.org/dist/v%s/node-v%s-darwin-x64.tar.gz' % (
                version, version)
        elif self.prefab.core.isUbuntu:
            url = 'https://nodejs.org/dist/v%s/node-v%s-linux-x64.tar.gz' % (
                version, version)

        else:
            raise j.exceptions.Input(message="only support ubuntu & mac")

        cdest = self.prefab.core.file_download(
            url, expand=True, overwrite=False, to="{DIR_TEMP}/node")

        self.core.run("rm -rf {DIR_BASE}/node;mv %s {DIR_BASE}/node" % (cdest))

        # if self.prefab.core.isMac:
        #     self.core.run('mv {DIR_BASE}/node/%s/* {DIR_BASE}/node' %
        #                   j.sal.fs.getBaseName(url.strip('.tar.gz')))

        self.prefab.bash.profileDefault.envSet("NODE_PATH", self.NODE_PATH)
        self.prefab.bash.profileDefault.addPath(self.prefab.core.replace("{DIR_BASE}/node/bin/"))
        self.prefab.bash.profileDefault.save()

        rc, out, err = self.prefab.core.run("npm -v", profile=True)
        if out != '5.3.0':  # 4.1.2
            # needs to be this version because is part of the package which was downloaded
            # self.prefab.core.run("npm install npm@4.1.2 -g", profile=True)
            raise RuntimeError("npm version error")

        rc, initmodulepath, err = self.prefab.core.run(
            "npm config get init-module", profile=True)
        self.prefab.core.file_unlink(initmodulepath)
        self.prefab.core.run("npm config set global true -g", profile=True)
        self.prefab.core.run(self.executor.replace(
            "npm config set init-module {DIR_BASE}/node/.npm-init.js -g"), profile=True)
        self.prefab.core.run(self.executor.replace(
            "npm config set init-cache {DIR_BASE}/node/.npm -g"), profile=True)
        self.prefab.core.run("npm config set global true ", profile=True)
        self.prefab.core.run(self.executor.replace(
            "npm config set init-module {DIR_BASE}/node/.npm-init.js "), profile=True)
        self.prefab.core.run(self.executor.replace(
            "npm config set init-cache {DIR_BASE}/node/.npm "), profile=True)
        self.prefab.core.run("npm install -g bower", profile=True, shell=True)

        # self.prefab.core.run("npm install npm@latest -g", profile=True)

        self.doneSet("install")
