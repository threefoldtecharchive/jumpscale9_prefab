from JumpScale import j
import textwrap

app = j.tools.cuisine._getBaseAppClass()


class CuisineApache(app):

    NAME = 'httpd'

    def build(self):
        return True

    def install(self):
        self.cuisine.package.ensure("apache2")
        self.cuisine.package.ensure("apache2-dev")
        # self.cuisine.package.ensure("libapache2-mod-php")

    def start(self):
        """start Apache."""
        self.cuisine.core.run("apachectl start")

    def stop(self):
        """stop Apache."""
        self.cuisine.core.run("apachectl stop")

    def restart(self):
        """restart Apache."""
        self.cuisine.core.run("apachectl restart")
