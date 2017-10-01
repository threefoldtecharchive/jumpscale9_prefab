from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabARDB(app):
    NAME = 'ardb'

    def reset(self):
        app.reset(self)
        self._init()

    def _init(self):
        self.BUILDDIRFDB = self.replace("$BUILDDIR/forestdb/")
        self.CODEDIRFDB = self.replace("$CODEDIR/github/couchbase/forestdb")
        self.CODEDIRARDB = self.replace("$CODEDIR/github/yinqiwen/ardb")
        self.BUILDDIRARDB = self.replace("$BUILDDIR/ardb/")

    def build(self, destpath="", reset=False):
        """
        @param destpath, if '' then will be $TMPDIR/build/openssl
        """
        if self.doneGet("build") and not reset:
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
        if self.doneGet("buildforestdb") and not reset:
            return

        self.prefab.system.package.multiInstall(["git-core",
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
            rm -rf $BUILDDIRFDB/
            mkdir -p $BUILDDIRFDB
            cp forestdb_dump* $BUILDDIRFDB/
            cp forestdb_hexamine* $BUILDDIRFDB/
            cp libforestdb* $BUILDDIRFDB/
            """
        self.prefab.core.run(self.replace(C))
        self.doneSet("buildforestdb")

    def buildARDB(self, reset=False, storageEngine="forestdb"):
        """
        @param storageEngine rocksdb or forestdb
        """
        if self.doneGet("buildardb") and not reset:
            return

        if self.prefab.platformtype.isMac:
            storageEngine = "rocksdb"
            # self.prefab.system.package.install("boost")

        # Default packages needed
        packages = ["wget", "bzip2"]

        # ForestDB
        packages += ["git-core", "cmake", "libsnappy-dev", "g++"]

        # RocksDB
        packages += ["libbz2-dev"]

        # PerconaFT
        packages += ["unzip"]

        # Install dependancies
        self.prefab.system.package.multiInstall(packages)


        url = "https://github.com/yinqiwen/ardb.git"
        cpath = self.prefab.tools.git.pullRepo(url, tag="v0.9.3", reset=reset, ssh=False)
        self.logger.info(cpath)

        assert cpath.rstrip("/") == self.CODEDIRARDB.rstrip("/")

        C = """
            set -ex
            cd $CODEDIRARDB
            # cp $BUILDDIRFDB/libforestdb* .
            storage_engine=$storageEngine make
            rm -rf $BUILDDIRARDB/
            mkdir -p $BUILDDIRARDB
            cp src/ardb-server $BUILDDIRARDB/
            cp ardb.conf $BUILDDIRARDB/
            """
        C = C.replace("$storageEngine", storageEngine)
        self.prefab.core.run(self.replace(C))

        self.doneSet("buildardb")

    def install(self, name='main', host='localhost', port=16379, datadir=None, reset=False, start=True):
        """
        as backend use ForestDB
        """
        if self.doneGet("install-%s" % name) and not reset:
            return
        self.buildARDB()
        self.prefab.core.dir_ensure("$BINDIR")
        self.prefab.core.dir_ensure("$CFGDIR")
        if not self.prefab.core.file_exists('$BINDIR/ardb-server'):
            self.core.file_copy("$BUILDDIR/ardb/ardb-server", "$BINDIR/ardb-server")

        self.prefab.bash.profileDefault.addPath('$BINDIR')

        if datadir is None or datadir == '':
            datadir = self.replace("$VARDIR/data/ardb/{}".format(name))
        self.core.dir_ensure(datadir)

        # config = config.replace("redis-compatible-mode     no", "redis-compatible-mode     yes")
        # config = config.replace("redis-compatible-version  2.8.0", "redis-compatible-version  3.5.2")
        config = self.core.file_read("$BUILDDIR/ardb/ardb.conf")
        config = config.replace("${ARDB_HOME}", datadir)
        config = config.replace("0.0.0.0:16379", '{host}:{port}'.format(host=host, port=port))

        cfg_path = "$CFGDIR/ardb/{}/ardb.conf".format(name)
        self.core.file_write(cfg_path, config)

        self.doneSet("install-%s" % name)

        if start:
            self.start(name=name, reset=reset)

    def start(self, name='main', reset=False):
        if not reset and self.doneGet("start-%s" % name):
            return

        cfg_path = "$CFGDIR/ardb/{}/ardb.conf".format(name)
        cmd = "$BINDIR/ardb-server {}".format(cfg_path)
        self.prefab.system.processManager.ensure(name="ardb-server-{}".format(name), cmd=cmd, env={}, path="")
        # self.test(port=port)

        self.doneSet("start-%s" % name)

    def stop(self, name='main'):
        self.prefab.system.processManager.stop("ardb-server-{}".format(name))

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
