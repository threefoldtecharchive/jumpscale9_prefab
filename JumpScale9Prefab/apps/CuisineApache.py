from js9 import j
import textwrap

app = j.tools.prefab._getBaseAppClass()


class CuisineApache(app):

    NAME = 'httpd'

    def build(self):
        return True

    def install(self):
        self.prefab.package.ensure("apache2")
        self.prefab.package.ensure("apache2-dev")
        # self.prefab.package.ensure("libapache2-mod-php")

    def start(self):
        """start Apache."""
        self.prefab.core.run("apachectl start")

    def stop(self):
        """stop Apache."""
        self.prefab.core.run("apachectl stop")

    def restart(self):
        """restart Apache."""
        self.prefab.core.run("apachectl restart")
