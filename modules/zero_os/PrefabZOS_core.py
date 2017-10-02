from js9 import j

# TODO: needs to be checked how this needs to be used, maybe no longer relevant in line to the building we do now

app = j.tools.prefab._getBaseAppClass()


class PrefabZOS_core(app):

    def build(self, start=True, gid=None, nid=None, install=True):
        """
        builds and setsup dependencies of agent to run , given gid and nid
        neither can be the int zero, can be ommited if start=False
        """
        # deps
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install('build-essential')
        # self.prefab.development.js8.installDeps()
        # self.prefab.apps.redis.install(reset=True)
        # self.prefab.apps.redis.start()
        # self.prefab.apps.mongodb.build(start=False)

        # self.prefab.apps.syncthing.build(start=False)

        self.prefab.system.tmux.killWindow("main", "agent")

        self.prefab.system.process.kill("agent")

        self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/agent", recursive=True)
        self.prefab.core.file_ensure("$TEMPLATEDIR/cfg/agent/.mid")

        url = "github.com/g8os/agent"
        self.prefab.runtimes.golang.godep(url)
        self.prefab.core.run("cd $GOPATHDIR/src/github.com/g8os/agent && go build -o superagent", profile=True)

        if install:
            self.install(start, gid, nid)

    def install(self, start=True, gid=None, nid=None):
        """
        download, install, move files to appropriate places, and create relavent configs
        """
        sourcepath = "$GOPATHDIR/src/github.com/g8os/agent"
        if not self.prefab.core.file_exists('$BINDIR/agent'):
            self.prefab.core.file_move("%s/superagent" % sourcepath, "$BINDIR/agent")

        # copy extensions
        self.prefab.core.dir_remove("$TEMPLATEDIR/cfg/agent/extensions")
        self.prefab.core.file_copy("%s/extensions" % sourcepath, "$TEMPLATEDIR/cfg/agent", recursive=True)
        self.prefab.core.file_copy("%s/g8os.toml" % sourcepath, "$TEMPLATEDIR/cfg/agent")
        self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/agent/conf/")
        config_source = '{0}basic.jumpscripts.toml {0}basic.syncthing.toml'.format(sourcepath + "/conf/")
        config_destination = '$TEMPLATEDIR/cfg/agent/conf/'
        self.prefab.core.file_copy(config_source, config_destination, recursive=True)
        if self.prefab.core.isArch:
            arch_config_src = '{0}sshd-arch.toml'.format(sourcepath + '/conf.extra/')
            arch_config_dest = '$TEMPLATEDIR/cfg/agent/conf/'
            self.prefab.core.file_copy(arch_config_src, arch_config_dest, recursive=True)
        if self.prefab.core.isUbuntu:
            ubuntu_config_src = '{0}sshd-ubuntu.toml'.format(sourcepath + '/conf.extra/')
            ubuntu_config_dest = '$TEMPLATEDIR/cfg/agent/conf/'
            self.prefab.core.file_copy(ubuntu_config_src, ubuntu_config_dest, recursive=True)
        self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/agent/extensions/syncthing")
        self.prefab.core.file_copy("$BINDIR/syncthing", "$TEMPLATEDIR/cfg/agent/extensions/syncthing/", recursive=True)

        if start:
            self.start(nid, gid)

    def start(self, gid, nid, controller_url="http://127.0.0.1:8966"):
        """
        if this is run on the sam e machine as a controller instance run controller first as the
        core will consume the avialable syncthing port and will cause a problem
        """

        # @todo this will break code if two instances on same machine
        if not nid:
            nid = 1
        if not gid:
            gid = 1

        self.prefab.core.dir_ensure('$JSCFGDIR/agent/')
        self.prefab.core.file_copy('$TEMPLATEDIR/cfg/agent', '$JSCFGDIR/', recursive=True)

        # manipulate config file
        sourcepath = '$TEMPLATEDIR/cfg/agent'
        C = self.prefab.core.file_read("%s/g8os.toml" % sourcepath)
        cfg = j.data.serializer.toml.loads(C)
        # Ubuntu: /optvar/cfg
        cfgdir = self.prefab.core.dir_paths['JSCFGDIR']
        cfg["main"]["message_ID_file"] = self.prefab.core.joinpaths(cfgdir, "/agent/.mid")
        cfg["main"]["include"] = self.prefab.core.joinpaths(cfgdir, "/agent/conf")
        cfg["main"].pop("network")
        cfg["controllers"] = {"main": {"url": controller_url}}
        extension = cfg["extension"]
        syncthing = extension['syncthing']
        syncthing['binary'] = '/optvar/cfg/agent/extensions/syncthing/syncthing'
        syncthing['cwd'] = '/optvar/cfg/agent/extensions'
        syncthing['env']['HOME'] = '/optvar/cfg/agent/extensions/syncthing'

        extension["sync"]["cwd"] = self.prefab.core.joinpaths(cfgdir, "/agent/extensions/sync")
        # Ubuntu: /optvar/cfg/core/extensions/jumpscript
        jumpscript_path = self.prefab.core.joinpaths(cfgdir, "/agent/extensions/jumpscript")
        extension["jumpscript"]["cwd"] = jumpscript_path
        extension["jumpscript_content"]["cwd"] = jumpscript_path
        extension["js_daemon"]["cwd"] = jumpscript_path
        extension["js_daemon"]["env"]["JUMPSCRIPTS_HOME"] = self.prefab.core.joinpaths(cfgdir, "/agent/jumpscripts/")
        cfg["logging"]["db"]["address"] = self.prefab.core.joinpaths(cfgdir, "/agent/logs")
        C = j.data.serializer.toml.dumps(cfg)

        self.prefab.core.file_write("$JSCFGDIR/agent/g8os.toml", C, replaceArgs=True)

        self.prefab.apps.mongodb.start()
        self.prefab.apps.redis.start()
        self.logger.info("connection test ok to agentcontroller")
        #@todo (*1*) need to implement to work on node
        env = {}
        env["TMPDIR"] = self.prefab.core.dir_paths["TMPDIR"]
        cmd = "$BINDIR/agent -nid %s -gid %s -c $JSCFGDIR/core/g8os.toml" % (
            nid, gid)
        pm = self.prefab.system.processManager.get('tmux')
        pm.ensure("agent", cmd=cmd, path="$JSCFGDIR/agent", env=env)
