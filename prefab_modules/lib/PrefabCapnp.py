from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabCapnp(app):

    NAME = "capnp"

    def build(self, reset=False):
        """
        install capnp

        js_shell 'j.tools.prefab.local.lib.capnp.build(reset=True)'

        """

        if self.doneGet('capnp') and not reset:
            return

        # self.prefab.system.package.mdupdate()
        self.prefab.system.installbase.development()
        if self.prefab.core.isUbuntu:
            self.prefab.system.package.install('g++')

        url="https://capnproto.org/capnproto-c++-0.6.1.tar.gz"
        dest = self.executor.replace("{DIR_VAR}/build/capnproto")
        self.prefab.core.createDir(dest)
        self.prefab.core.file_download(url, to=dest, overwrite=False, retry=3,
                    expand=True, minsizekb=900, removeTopDir=True, deletedest=True)

        script = """
        cd {DIR_VAR}/build/capnproto
        ./configure
        make -j6 check
        make install
        """
        self.prefab.core.run(script)

        self.doneSet('capnp')


    def install(self):
        self.build()
        self.prefab.runtimes.pip.multiInstall(['cython', 'setuptools', 'pycapnp'], upgrade=True)


        self.doneSet('capnp')
