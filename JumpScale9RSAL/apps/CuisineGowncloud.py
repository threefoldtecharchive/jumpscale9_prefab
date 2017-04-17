from JumpScale import j
import textwrap
import re
app = j.tools.cuisine._getBaseAppClass()


class CuisineGowncloud(app):

    NAME = 'gowncloud'

    def build(self):
        """
        build gowncloud and build
        """
        self.cuisine.development.golang.get("github.com/gowncloud/gowncloud")
        self._cuisine.core.file_copy("$goDir/bin/gowncloud", "$binDir")

    def start(self, client_id, client_secret, db_driver='postgres', db_user='postgres', db_url='localhost', db_port='5432', sslmode='disable'):
        self.cuisine.core.run("$binDir/gowncloud -c {client_id} -s {client_secret} --db {db_driver}://{db_user}@{db_url}:{db_port}?sslmode={sslmode}".format(
          client_id=client_id,
          client_secret=client_secret,
          db_driver=db_driver,
          db_user=db_user,
          db_url=db_url,
          db_port=db_port,
          sslmode=sslmode))
