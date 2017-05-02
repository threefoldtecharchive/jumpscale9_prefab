from js9 import j

base = j.tools.prefab._getBaseClass()


class CuisineLibffi(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/libffi/")
        self.CODEDIRL = self.core.replace("$CODEDIR/github/libffi/libffi/")

    def reset(self):
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)

    def build(self, destpath="", reset=False):
        """
        @param destpath, if '' then will be $TMPDIR/build/openssl
        """
        if reset:
            self.reset()

        if self.doneGet("build") and not reset:
            return

        self.prefab.package.mdupdate()
        self.prefab.core.dir_ensure(self.BUILDDIRL)
        self.prefab.package.multiInstall(['build-essential', 'dh-autoreconf'])
        url = "https://github.com/libffi/libffi.git"
        cpath = self.prefab.development.git.pullRepo(url, reset=reset, ssh=False)

        assert cpath.rstrip("/") == self.CODEDIRL.rstrip("/")

        if not self.doneGet("compile") or reset:
            C = """
            set -ex
            cd $CODEDIRL
            ./autogen.sh
            ./configure  --prefix=$BUILDDIRL --disable-docs
            make
            make install
            """
            self.prefab.core.run(self.replace(C))
            self.doneSet("compile")
            self.logger.info("BUILD DONE")
        else:
            self.logger.info("NO NEED TO BUILD")

        self.logger.info("BUILD COMPLETED OK")
        self.doneSet("build")
