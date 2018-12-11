from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabLibffi(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/libffi")
        self.CODEDIRL = self.core.replace("$BUILDDIR/code/libffi")

    def reset(self):
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)

    def build(self, reset=False):
        """
        js_shell 'j.tools.prefab.local.lib.libffi.build(reset=True)'
        """
        if reset:
            self.reset()

        if self.doneGet("build") and not reset:
            return

        self.prefab.system.package.mdupdate()
        self.prefab.core.dir_ensure(self.BUILDDIRL)
        if not self.core.isMac:
            self.prefab.system.package.install('dh-autoreconf')
        url = "https://github.com/libffi/libffi.git"
        self.prefab.tools.git.pullRepo(url, reset=False, dest=self.CODEDIRL, ssh=False)

        if not self.doneGet("compile") or reset:
            C = """
            set -ex
            mkdir -p $BUILDDIRL
            cd $CODEDIRL
            ./autogen.sh
            ./configure  --prefix=$BUILDDIRL --disable-docs
            make
            make install
            """
            self.prefab.core.file_write("%s/mycompile_all.sh" % self.CODEDIRL, self.replace(C))
            self.logger.info("compile libffi")
            self.logger.debug(C)
            self.prefab.core.run("sh %s/mycompile_all.sh" % self.CODEDIRL)
            self.doneSet("compile")
            self.logger.info("BUILD DONE")
        else:
            self.logger.info("NO NEED TO BUILD")

        self.logger.info("BUILD COMPLETED OK")
        self.doneSet("build")
