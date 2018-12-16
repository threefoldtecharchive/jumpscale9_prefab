from Jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabARDB(app):
    NAME = 'ardb'

    def reset(self):
        app.reset(self)
        self._init()

    def _init(self):
        self.BUILDDIRFDB = self.executor.replace("{DIR_VAR}/build/forestdb/")
        self.CODEDIRFDB = self.executor.replace("$CODEDIR/github/couchbase/forestdb")
        self.CODEDIRARDB = self.executor.replace("$CODEDIR/github/yinqiwen/ardb")
        self.BUILDDIRARDB = self.executor.replace("{DIR_VAR}/build/ardb/")

    def build(self, destpath="", reset=False):
        """
        @param destpath, if '' then will be {DIR_TEMP}/build/openssl
        """
        if self.doneCheck("build", reset):
            return

        if self.prefab.bash.cmdGetPath('ardb-server', die=False) and not reset:
            return

        if reset:
            self.prefab.core.run("rm -rf %s" % self.BUILDDIR)

        # not needed to build separately is done in ardb automatically
        # self.buildForestDB(reset=reset)

        self.buildARDB(reset=reset)
        self.doneSet("build")

    def buildForestDB(self, reset=False):

        if self.doneCheck("buildforestdb", reset):
            return

        self.prefab.system.package.install(["git-core",
                                                 "cmake",
                                                 "libsnappy-dev",
                                                 "g++"])

        url = "git@github.com:couchbase/forestdb.git"
        cpath = self.prefab.tools.git.pullRepo(url, tag="v1.2", reset=reset)

        assert cpath.rstrip("/") == self.CODEDIRFDB.rstrip("/")

        C = """
            set -ex
            cd $CODEDIRFDB
            mkdir build
            cd build
            cmake ../
            make all
            rm -rf {DIR_VAR}/build/FDB/
            mkdir -p {DIR_VAR}/build/FDB
            cp forestdb_dump* {DIR_VAR}/build/FDB/
            cp forestdb_hexamine* {DIR_VAR}/build/FDB/
            cp libforestdb* {DIR_VAR}/build/FDB/
            """
        self.prefab.core.run(self.executor.replace(C))
        self.doneSet("buildforestdb")

    def build(self, reset=False, storageEngine="forestdb"):
        """
        js_shell 'j.tools.prefab.local.db.ardb.build()'

        @param storageEngine rocksdb or forestdb
        """
        if self.doneCheck("buildardb", reset):
            return

        # Default packages needed
        packages = ["wget", "bzip2"]

        if self.prefab.platformtype.isMac:
            storageEngine = "rocksdb"
            # ForestDB
            packages += ["git", "cmake", "libsnappy-dev", "gcc48"]
            # self.prefab.system.package.install("boost")
        else:
            # ForestDB
            packages += ["git", "cmake", "libsnappy-dev", "g++"]
            # RocksDB
            packages += ["libbz2-dev"]

        # PerconaFT
        packages += ["unzip"]

        # Install dependancies
        self.prefab.system.package.install(packages)

        url = "https://github.com/yinqiwen/ardb.git"
        cpath = self.prefab.tools.git.pullRepo(
            url, tag="v0.9.3", reset=reset, ssh=False)
        self.logger.info(cpath)

        assert cpath.rstrip("/") == self.CODEDIRARDB.rstrip("/")

        C = """
            set -ex
            cd $CODEDIRARDB
            # cp {DIR_VAR}/build/FDB/libforestdb* .
            storage_engine=$storageEngine make
            rm -rf {DIR_VAR}/build/ARDB/
            mkdir -p {DIR_VAR}/build/ARDB
            cp src/ardb-server {DIR_VAR}/build/ARDB/
            cp ardb.conf {DIR_VAR}/build/ARDB/
            """
        C = C.replace("$storageEngine", storageEngine)
        self.prefab.core.execute_bash(self.executor.replace(C))

        self.doneSet("buildardb")

    def install(self, name='main', host='localhost', port=16379, datadir=None, reset=False, start=True):
        """
        as backend use ForestDB
        """
        if self.doneCheck("install-%s" % name, reset):
            return
        self.buildARDB()
        self.prefab.core.dir_ensure("{DIR_BIN}")
        self.prefab.core.dir_ensure("$CFGDIR")
        if not self.prefab.core.file_exists('{DIR_BIN}/ardb-server'):
            self.core.file_copy("{DIR_VAR}/build/ardb/ardb-server",
                                "{DIR_BIN}/ardb-server")

        self.prefab.bash.profileDefault.addPath('{DIR_BIN}')

        if datadir is None or datadir == '':
            datadir = self.executor.replace("{DIR_VAR}/data/ardb/{}".format(name))
        self.core.dir_ensure(datadir)

        # config = config.replace("redis-compatible-mode     no", "redis-compatible-mode     yes")
        # config = config.replace("redis-compatible-version  2.8.0", "redis-compatible-version  3.5.2")
        config = self.core.file_read("{DIR_VAR}/build/ardb/ardb.conf")
        config = config.replace("${ARDB_HOME}", datadir)
        config = config.replace(
            "0.0.0.0:16379", '{host}:{port}'.format(host=host, port=port))

        cfg_path = "$CFGDIR/ardb/{}/ardb.conf".format(name)
        self.core.file_write(cfg_path, config)

        self.doneSet("install-%s" % name)

        if start:
            self.start(name=name, reset=reset)

    def start(self, name='main', reset=False):
        if not reset and self.doneGet("start-%s" % name):
            return

        cfg_path = "$CFGDIR/ardb/{}/ardb.conf".format(name)
        cmd = "{DIR_BIN}/ardb-server {}".format(cfg_path)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="ardb-server-{}".format(name), cmd=cmd, env={}, path="")
        # self.test(port=port)

        self.doneSet("start-%s" % name)

    def stop(self, name='main'):
        pm = self.prefab.system.processmanager.get()
        pm.stop("ardb-server-{}".format(name))

    def getClient(self):
        pass

    def test(self, port):
        """
        do some test through normal redis client
        """
        if self.prefab.executor.type == 'local':
            addr = 'localhost'
        else:
            addr = self.prefab.executor.addr

        r = j.clients.redis.get(ipaddr=addr, port=port)
        r.set("test", "test")
        assert r.get("test") == b"test"
        r.delete("test")
