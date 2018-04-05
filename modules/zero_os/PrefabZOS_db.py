from js9 import j

app = j.tools.prefab._getBaseAppClass()

SUPPORTED_MODE = ['user', 'seq', 'direct']


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

        path = self.prefab.tools.git.pullRepo('https://github.com/rivine/0-db')
        self.prefab.core.run("cd %s; git reset --hard HEAD~10 && git pull"%path)

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

    def start(self, instance='main', host='localhost', port=9900, index="/tmp/zdb-index", data="/tmp/zdb-data", mode='user', verbose=True, adminsecret=""):
        if mode not in SUPPORTED_MODE:
            raise ValueError("mode %s is not supported" % mode)

        pm = self.prefab.system.processmanager.get()
        cmdline = "$BINDIR/zdb --listen %s --port %s --index %s --data %s --mode %s" % (host, port, index, data, mode)

        if adminsecret is not "":
            cmdline += " --admin %s" % adminsecret

        if verbose:
            cmdline += " -v"

        pm.ensure('%s_0db' % instance, cmd=cmdline)

    def stop(self, instance='main'):
        pm = self.prefab.system.processmanager.get()
        pm.stop('%s_0db' % instance)
