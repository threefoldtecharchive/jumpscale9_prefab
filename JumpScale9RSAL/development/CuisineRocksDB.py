from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineRocksDB(base):

    # WIP : builds but still cannot install gorocksdb yet , based on
    # https://github.com/g8os/initramfs/blob/0.12.0/internals/gorocksdb.sh
    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/rocksdb/")
        self.ROCKSDB_VERSION = "5.1.2"
        self.ROCKSDB_LINK = "https://github.com/facebook/rocksdb/archive/v%s.tar.gz" % self.ROCKSDB_VERSION

    def build(self, reset=True, install=True):
        # Get binaries and build rocksdb.
        if self.doneGet("build") and not reset:
            return

        self.cuisine.core.dir_ensure(self.BUILDDIRL)

        # install deps
        self.cuisine.package.mdupdate()
        self.cuisine.package.install('build-essential')
        self.cuisine.package.install('libsnappy-dev')
        self.cuisine.package.install('zlib1g-dev')
        self.cuisine.package.install('libbz2-dev')
        self.cuisine.package.install('libzstd-dev')
        self.cuisine.package.install('librocksdb-dev')

        # set env variables
        profile = self.cuisine.bash.profileDefault
        profile.envSet("ROCKSDB_VERSION", self.ROCKSDB_VERSION)
        profile.envSet("ROCKSDB_LINK", self.ROCKSDB_LINK)
        profile.envSet("ROCKSDB_CHECKSUM", "b682f574363edfea0e2f7dbf01fc0e5b")
        profile.envSet("CGO_CFLAGS", "-I%s/rocksdb-%s/include" % (self.BUILDDIRL, self.ROCKSDB_VERSION))
        profile.envSet("CGO_LDFLAGS",
                       "-L%s/rocksdb-%s -lrocksdb -lstdc++ -lm -lz -lbz2 -lsnappy -llz4" % (self.BUILDDIRL,
                                                                                            self.ROCKSDB_VERSION))
        profile.save()

        # download gorocksdb
        self.cuisine.core.file_download('%s' % self.ROCKSDB_LINK, '$TMPDIR/rocksdb-%s.tar.gz' % self.ROCKSDB_VERSION)

        # extract rocksdb
        if not self.cuisine.core.file_exists('$TMPDIR/rocksdb-%s.tar.gz' % self.ROCKSDB_VERSION):
            raise RuntimeError('could not find tar of rocksdb')
        self.cuisine.core.run('cd $TMPDIR && tar -xf rocksdb-%s.tar.gz -C .' % self.ROCKSDB_VERSION)

        # compile and install
        self.cuisine.core.run('cd $TMPDIR/rocksdb-%s && PORTABLE=1 make shared_lib' % self.ROCKSDB_VERSION,
                              profile=True)
        self.cuisine.core.run('cd $TMPDIR/rocksdb-%s && cp -a librocksdb.so* %s' % (self.ROCKSDB_VERSION,
                                                                                    self.BUILDDIRL))
        self.cuisine.core.run('cd $TMPDIR/rocksdb-%s && cp -a librocksdb.so* /usr/lib' % self.ROCKSDB_VERSION)
        # self.cuisine.development.golang.get('github.com/tecbot/gorocksdb', tags=['embed'])

        self.doneSet("build")

        if install:
            self.install()

    def install(self):
        # install required packages to run.
        self.cuisine.package.install("libhiredis-dev")
        self.cuisine.package.install("libbz2-dev")
        self.cuisine.package.install('python3-dev')
        self.cuisine.development.pip.ensure()
        self.cuisine.development.pip.multiInstall(['pyrocksdb', 'peewee'])
