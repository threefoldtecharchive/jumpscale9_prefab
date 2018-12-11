
from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabNIM(base):
    """
    """

    def _init(self):
        self.logger_enable()
        self.BUILDDIRL = self.core.replace("$BUILDDIR/nimlang/")
        self.CODEDIRL = self.core.replace("$BUILDDIR/code/nimlang/")

    def build(self, reset=False):
        """
        js_shell 'j.tools.prefab.local.runtimes.nim.build(reset=False)'
        :return:
        """

        if reset:
            self.reset()

        if self.doneCheck("build", reset):
            return

        url = "https://nim-lang.org/download/nim-0.19.0.tar.xz"

        self.prefab.core.file_download(url, to=self.CODEDIRL, overwrite=False,
                                       expand=True, minsizekb=400, removeTopDir=True, deletedest=True)

        C = """
        cd $CODEDIRL
        export LDFLAGS="-L/usr/local/opt/openssl/lib"
        export CPPFLAGS="-I/usr/local/opt/openssl/include"
        export DYLD_LIBRARY_PATH=/usr/local/opt/openssl/lib
        sh build.sh
        sh install.sh ~/.nimble/
        bin/nim c koch
        ./koch tools
        """

        self.core.execute_bash(self.replace(C))
