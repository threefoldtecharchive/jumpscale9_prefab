from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabZOS_db(app):
    """
    0-db key-value store
    """
    NAME = 'db'

    def build(self, debug=False, start=False, install=True, reset=False):
        if reset is False and self.isInstalled():
            return

        if self.prefab.core.isUbuntu:
            self.prefab.system.package.mdupdate()
            self.prefab.system.package.install('build-essential')

        path = self.prefab.tools.git.pullRepo('https://github.com/zero-os/0-db')

        make = "make" if debug else "make release"
        self.prefab.core.run("cd %s && make clean && %s" % (path, make))

        if install:
            self.install(path, start)

    def install(self, source=None, start=False):
        if not source:
            raise j.exceptions.RuntimeError("Please provide source-code path")

        self.prefab.core.file_copy("%s/bin/*" % source, "$BASEDIR/bin/")

        if start:
            self.start()

    def start(self, index="/tmp/zdb-index", data="/tmp/zdb-data", verbose=True):
        # FIXME: add mode selection
        pm = self.prefab.system.processmanager.get()
        cmdline = "$BINDIR/zdb --index %s --data %s" % (index, data)

        if verbose:
            cmdline += " -v"

        pm.ensure('0db', cmd=cmdline)
