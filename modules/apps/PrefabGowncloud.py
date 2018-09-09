from Jumpscale import j
import textwrap
import re
app = j.tools.prefab._getBaseAppClass()


class PrefabGowncloud(app):

    def build(self):
        """
        build gowncloud and build
        """
        if self.doneCheck("build"):
            return
        self.prefab.runtimes.golang.install()
        self.prefab.runtimes.golang.bindata()

        gopath = self.prefab.runtimes.golang.GOPATH
        dest = "{gopath}/src/github.com/gowncloud/gowncloud".format(gopath=gopath)
        # self.prefab.core.run('mkdir -p {dest}'.format(dest=dest))
        self.prefab.tools.git.pullRepo("https://github.com/gowncloud/gowncloud.git", dest=dest, ssh=False)
        self.prefab.core.run('cd {dest} && go generate && go build'.format(dest=dest), profile=True)
        self.prefab.core.file_copy("{dest}/gowncloud".format(dest=dest), "$BINDIR")
        self.doneSet('build')


    def install(self, reset=False):
        """
        Install method
        """
        return self.build()



    def start(
            self,
            client_id,
            client_secret,
            db_driver='postgres',
            db_user='root',
            db_url='localhost',
            # db_port='5432',
            db_port='26257',
            sslmode='disable'):
        pm = self.prefab.system.processmanager.get()
        pm.ensure("gowncloud", "$BINDIR/gowncloud -c {client_id} -s {client_secret} --db {db_driver}://{db_user}@{db_url}:{db_port}?sslmode={sslmode}".format(
            client_id=client_id,
            client_secret=client_secret,
            db_driver=db_driver,
            db_user=db_user,
            db_url=db_url,
            db_port=db_port,
            sslmode=sslmode))

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("gowncloud")
