from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabBrotli(app):

    NAME = 'bro'

    def build(self, reset=False):
        if reset is False and self.isInstalled():
            return
        sudo = 'sudo'
        if self.prefab.core.isMac:
            sudo = ''
        C = """
        cd /tmp
        %s rm -rf brotli/
        git clone https://github.com/google/brotli.git
        cd /tmp/brotli/
        ./configure
        make bro
        """ % sudo
        C = self.replace(C)
        self.prefab.core.run(C)

    def install(self, reset=False):
        if reset is False and self.isInstalled():
            return
        C = """
        cp /tmp/brotli/bin/bro /usr/local/bin/
        rm -rf /tmp/brotli
        """
        self.prefab.core.run(C)
        self.prefab.development.pip.install('brotli>=0.5.2')
