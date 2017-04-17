from JumpScale import j
import os

app = j.tools.cuisine._getBaseAppClass()


class CuisineLedis(app):
    NAME = "ledis-server"

    def build(self, backend="leveldb", install=True, start=True, reset=False):
        if reset is False and self.isInstalled():
            return

        if self.cuisine.core.isUbuntu:

            C = """
            #!/bin/bash
            set -x

            cd {ledisdir}
            #set build and run environment
            source dev.sh

            make
            """
            self.cuisine.development.golang.install()
            self.cuisine.development.git.pullRepo("https://github.com/siddontang/ledisdb",
                                                   dest="$GOPATHDIR/src/github.com/siddontang/ledisdb")

            # set the backend in the server config
            ledisdir = self.replace("$GOPATHDIR/src/github.com/siddontang/ledisdb")

            configcontent = self.cuisine.core.file_read(os.path.join(ledisdir, "config", "config.toml"))
            ledisdir = self.replace("$GOPATHDIR/src/github.com/siddontang/ledisdb")

            if backend == "rocksdb":
                self._preparerocksdb()
            elif backend == "leveldb":
                rc, out, err = self._prepareleveldb()
            else:
                raise NotImplementedError
            configcontent.replace('db_name = "leveldb"', 'db_name = "%s"' % backend)

            self.cuisine.core.file_write("/tmp/ledisconfig.toml", configcontent)

            script = C.format(ledisdir=ledisdir)
            out = self.cuisine.core.run(script, profile=True)

            if install:
                self.install(start=True)

    def _prepareleveldb(self):
        # execute the build script in tools/build_leveldb.sh
        # it will install snappy/leveldb in /usr/local{snappy/leveldb} directories
        ledisdir = self.replace("$GOPATHDIR/src/github.com/siddontang/ledisdb")
        # leveldb_build file : ledisdir/tools/build_leveldb.sh
        rc, out, err = self.cuisine.core.run("bash {ledisdir}/tools/build_leveldb.sh".format(ledisdir=ledisdir))
        return rc, out, err

    def _preparerocksdb(self):
        raise NotImplementedError

    def install(self, start=True):
        ledisdir = self.replace("$GOPATHDIR/src/github.com/siddontang/ledisdb")

        #rc, out, err = self.cuisine.core.run("cd {ledisdir} && source dev.sh && make install".format(ledisdir=ledisdir), profile=True)
        self.cuisine.core.dir_ensure("$TEMPLATEDIR/cfg")
        self.cuisine.core.file_copy("/tmp/ledisconfig.toml", dest="$TEMPLATEDIR/cfg/ledisconfig.toml")
        self.cuisine.core.file_copy("{ledisdir}/bin/*".format(ledisdir=ledisdir), dest="$BINDIR")
        self.cuisine.core.file_copy("{ledisdir}/dev.sh".format(ledisdir=ledisdir), dest="$TEMPLATEDIR/ledisdev.sh")

        if start:
            self.start()

    def start(self):
        cmd = "source $TEMPLATEDIR/ledisdev.sh && $BINDIR/ledis-server -config $TEMPLATEDIR/cfg/ledisconfig.toml"
        pm = self.cuisine.processmanager.get("tmux")
        pm.ensure(name='ledis', cmd=cmd)
