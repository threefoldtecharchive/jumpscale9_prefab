from js9 import j

app = j.tools.prefab._getBaseAppClass()

# TODO: is this still correct, maybe our docker approach better, need to check


class Prefabjs9Core(app):
    NAME = 'js9'


    def install(self,reset=False):
        """
        j.tools.prefab.local.js9.js9Core.install()

        or from bash

        js9_prefab 'js9.js9core.install reset=1'

        """
        if j.data.serializer.fixType(reset,False)==False and self.isInstalled():
            return

        S="""
        echo "INSTALL BASHTOOLS"
        curl https://raw.githubusercontent.com/Jumpscale/bash/master/install.sh?$RANDOM > /tmp/install.sh
        
        bash /tmp/install.sh || echo "could not install bash tools" && exit 1

        echo "load zlibs"
        source ~/code/github/jumpscale/bash/zlibs.sh 2>&1 > /dev/null
        source /opt/code/github/jumpscale/bash/zlibs.sh 2>&1 > /dev/null
        ZDoneReset

        echo "install js9"
        ZInstall_host_js9 || die "Could not install core9 of js9" || exit 1

        pip3 install Cython
        pip3 install asyncssh
        pip3 install numpy
        pip3 install tarantool
        """
        self.core.execute_bash(S)



        
