from JumpScale import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineCapnp(app):

    NAME = "capnp"

    def install(self, reset=False):
        """
        install capnp
        """

        if reset is False and self.isInstalled():
            return

        self.cuisine.package.mdupdate()
        self.cuisine.package.multiInstall(['curl', 'make', 'g++', 'python-dev'])

        #@TODO: *2 use git checkout on tag like we do for ARDB

        # c++ deps libs
        script = """
        cd $TMPDIR
        curl -O https://capnproto.org/capnproto-c++-0.5.3.tar.gz
        tar zxf capnproto-c++-0.5.3.tar.gz
        cd capnproto-c++-0.5.3
        ./configure
        make -j6 check
        sudo make install
        """
        self.cuisine.core.run(script)
        # install python pacakge
        self.cuisine.development.pip.multiInstall(['cython', 'setuptools', 'pycapnp'], upgrade=True)
