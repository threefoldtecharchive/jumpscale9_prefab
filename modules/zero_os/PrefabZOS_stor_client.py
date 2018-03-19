from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabZOS_stor_client(base):
    def build(self):
        builddir = '/tmp/buildg8client'
        self.prefab.tools.git.pullRepo('https://github.com/maxux/lib0stor', dest=builddir)
        self.prefab.core.run('cd {}; git submodule init; git submodule update'.format(builddir))

        self.prefab.system.package.ensure('build-essential libz-dev libssl-dev python3-dev libsnappy-dev')

        self.prefab.lib.cmake.install()
        self.prefab.core.run('cd {}; make -C src'.format(builddir))

        self.prefab.core.run('cd {}/python/; python3 setup.py build'.format(builddir))

    def install(self):
        return self.build()
