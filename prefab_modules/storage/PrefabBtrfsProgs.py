from Jumpscale import j
from JumpscalePrefab.PrefabFactory import PrefabApp


class PrefabBtrfsProgs(PrefabApp):
    NAME = 'btrfs'

    # depends of: pkg-config build-essential e2fslibs-dev libblkid-dev liblzo2-dev

    def _init(self):
        # if the module builds something, define BUILDDIR and CODEDIR folders.
        self.BUILDDIR = self.core.replace("{DIR_VAR}/build/btrfs-progs/")
        self.CODEDIR = self.core.replace("{DIR_CODE}")

        self._host = "https://www.kernel.org/pub/linux/kernel/people/kdave/btrfs-progs"
        self._file = "btrfs-progs-v4.8.tar.xz"

    def _run(self, command):
        return self.prefab.core.run(self.executor.replace(command))

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        super().reset()
        self.core.dir_remove(self.BUILDDIR)
        self.core.dir_remove(self.CODEDIR + 'btrfs-progs-v4.8')
        self.doneDelete('build')
        self._run("cd $LIBDIR; rm -f libbtrfs.so.0.1")
        self._run("cd $LIBDIR; rm -f libbtrfs.so.0")
        self._run("rm -f {DIR_BIN}/btrfs")
        self.prefab.runtimes.pip.reset()

    def build(self, reset=False):
        if reset is False and (self.isInstalled() or self.doneGet('build')):
            return
        self.core.run('apt-get -y install asciidoc xmlto --no-install-recommends')
        deps = """
        uuid-dev libattr1-dev zlib1g-dev libacl1-dev e2fslibs-dev libblkid-dev liblzo2-dev autoconf
        """
        self.prefab.system.package.install(deps)
        self._run("cd {DIR_TEMP}; wget -c %s/%s" % (self._host, self._file))
        self._run("cd {DIR_TEMP}; tar -xf %s -C {DIR_CODE}" % self._file)
        self._run("cd {DIR_CODE}/btrfs-progs-v4.8; ./autogen.sh")
        self._run("cd {DIR_CODE}/btrfs-progs-v4.8; ./configure --prefix={DIR_VAR}/build/ --disable-documentation")
        self._run("cd {DIR_CODE}/btrfs-progs-v4.8; make")
        self._run("cd {DIR_CODE}/btrfs-progs-v4.8; make install")

        self.doneSet('build')

    def install(self, reset=False):
        # copy binaries, shared librairies, configuration templates,...
        self.prefab.core.file_copy(self.executor.replace("{DIR_VAR}/build/bin/btrfs"), '{DIR_BIN}')

        self.prefab.core.file_copy(self.executor.replace("{DIR_VAR}/build/lib/libbtrfs.so"), '$LIBDIR')
        self._run("cd $LIBDIR; ln -s libbtrfs.so libbtrfs.so.0.1")
        self._run("cd $LIBDIR; ln -s libbtrfs.so libbtrfs.so.0")

    def start(self, name):
        pass

    def stop(self, name):
        pass

    def getClient(self, executor=None):
        return j.sal.btrfs.getBtrfs(executor)
