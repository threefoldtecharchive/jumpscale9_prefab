from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabZOS_controller(app):
    NAME = "controller"

    def build(self, start=True, listen_addr=[], install=True, reset=False):
        """
        config: https://github.com/g8os/controller.git
        """
        if reset is False and self.isInstalled():
            return
        # deps
        deps = ['redis-server', 'syncthing']
        for dep in deps:
            if not self.prefab.core.command_check(dep):
                raise j.exceptions.NotFound(
                    "dependency %s not found, please install %s before building controller" % (dep, dep))
        # self.prefab.apps.redis.install()
        # self.prefab.apps.syncthing.build(start=False)

        self.prefab.system.processmanager.remove("agentcontroller8")
        pm = self.prefab.system.processmanager.get("tmux")
        pm.stop("syncthing")

        self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/controller", recursive=True)

        # get repo
        url = "github.com/g8os/controller"
        self.prefab.runtimes.golang.clean_src_path()
        self.prefab.runtimes.golang.godep(url)

        # Do the actual building
        self.prefab.core.run("cd $GOPATHDIR/src/github.com/g8os/controller && go build .", profile=True)

        if install:
            self.install(start, listen_addr)

    def install(self, start=True, listen_addr=[]):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        sourcepath = "$GOPATHDIR/src/github.com/g8os/controller"
        # move binary
        if not self.prefab.core.file_exists('$BINDIR/controller'):
            self.prefab.core.file_move("%s/controller" % sourcepath, "$BINDIR/controller")

        # file copy
        self.prefab.core.dir_remove("$TEMPLATEDIR/cfg/controller/extensions")

        jumpscript_folfer = "%s/github/jumpscale/jumpscale_core9/apps/agentcontroller/jumpscripts" % self.prefab.core.dir_paths[
            "CODEDIR"]
        if self.prefab.core.dir_exists(jumpscript_folfer):
            self.prefab.core.file_copy(jumpscript_folfer + "/jumpscale",
                                        "$TEMPLATEDIR/cfg/controller/jumpscripts/", recursive=True)

        self.prefab.core.file_copy("%s/extensions" % sourcepath,
                                    "$TEMPLATEDIR/cfg/controller/extensions", recursive=True)

        self.prefab.core.file_copy("%s/agentcontroller.toml" % sourcepath,
                                    '$TEMPLATEDIR/cfg/controller/agentcontroller.toml')

        if start:
            self.start(listen_addr=listen_addr)

    def start(self, listen_addr=[]):
        """
        @param listen_addr list of addresse on which the REST API of the controller should listen to
        e.g: [':80', '127.0.0.1:888']
        """
        import hashlib
        from xml.etree import ElementTree

        self.prefab.core.dir_ensure("$JSCFGDIR/controller/")
        self.prefab.core.file_copy("$TEMPLATEDIR/cfg/controller", "$JSCFGDIR/", recursive=True, overwrite=True)

        # edit config
        C = self.prefab.core.file_read('$JSCFGDIR/controller/agentcontroller.toml')
        cfg = j.data.serializer.toml.loads(C)

        listen = cfg['listen']
        for addr in listen_addr:
            listen.append({'address': addr})

        cfgDir = self.prefab.core.dir_paths['JSCFGDIR']
        cfg["events"]["python_path"] = self.prefab.core.joinpaths(
            cfgDir, "/controller/extensions:/opt/jumpscale9/lib")
        cfg['events']['enabled'] = True
        cfg["processor"]["python_path"] = self.prefab.core.joinpaths(
            cfgDir, "/controller/extensions:/opt/jumpscale9/lib")
        cfg["jumpscripts"]["python_path"] = self.prefab.core.joinpaths(
            cfgDir, "/controller/extensions:/opt/jumpscale9/lib")
        cfg["jumpscripts"]["settings"]["jumpscripts_path"] = self.prefab.core.joinpaths(
            cfgDir, "/controller/jumpscripts")
        C = j.data.serializer.toml.dumps(cfg)

        self.prefab.core.file_write('$JSCFGDIR/controller/agentcontroller.toml', C, replaceArgs=True)

        # expose syncthing and get api key
        sync_cfg = ElementTree.fromstring(self.prefab.core.file_read("$TEMPLATEDIR/cfg/syncthing/config.xml"))
        sync_id = sync_cfg.find('device').get('id')

        # set address
        sync_cfg.find("./gui/address").text = '127.0.0.1:18384'

        jumpscripts_id = "jumpscripts-%s" % hashlib.md5(sync_id.encode()).hexdigest()
        jumpscripts_path = self.replace("$JSCFGDIR/controller/jumpscripts")

        # find folder element
        configured = False
        for folder in sync_cfg.findall('folder'):
            if folder.get('id') == jumpscripts_id:
                configured = True
                break

        if not configured:
            folder = ElementTree.SubElement(sync_cfg, 'folder', {
                'id': jumpscripts_id,
                'path': jumpscripts_path,
                'ro': 'true',
                'rescanIntervalS': '60',
                'ignorePerms': 'false',
                'autoNormalize': 'false'
            })

            ElementTree.SubElement(folder, 'device', {'id': sync_id})
            ElementTree.SubElement(folder, 'minDiskFreePct').text = '1'
            ElementTree.SubElement(folder, 'versioning')
            ElementTree.SubElement(folder, 'copiers').text = '0'
            ElementTree.SubElement(folder, 'pullers').text = '0'
            ElementTree.SubElement(folder, 'hashers').text = '0'
            ElementTree.SubElement(folder, 'order').text = 'random'
            ElementTree.SubElement(folder, 'ignoreDelete').text = 'false'

        dump = ElementTree.tostring(sync_cfg, 'unicode')
        j.logger.info("SYNCTHING CONFIG", level=10)
        j.logger.info(dump, level=10)
        self.prefab.core.file_write("$JSCFGDIR/syncthing/config.xml", dump)

        # start
        pm = self.prefab.apps.syncthing.restart()

        env = {}
        env["TMPDIR"] = self.prefab.core.dir_paths["TMPDIR"]
        cmd = "$BINDIR/controller -c $JSCFGDIR/controller/agentcontroller.toml"
        pm = self.prefab.system.processmanager.get("tmux")
        pm.ensure("controller", cmd=cmd, path="$JSCFGDIR/controller/", env=env)
