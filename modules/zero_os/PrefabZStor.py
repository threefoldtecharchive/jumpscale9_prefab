from jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabZStor(app):
    NAME = 'zstor'

    def build(self):
        if not self.prefab.runtimmes.golang.isInstalled():
            self.logger.info('install golang')
            self.prefab.runtimmes.golang.install(reset=False, old=False)

        self.logger.info("install zstor daemon")
        self.prefab.runtimmes.golang.get('github.com/threefoldtech/0-stor/cmd/zstor')

        self.logger.info("install zstor dameon client")
        dest = self.prefab.tools.git.pullRepo('https://github.com/threefoldtech/0-stor.git', ssh=False)
        client_path = j.sal.fs.joinPaths(dest, 'daemon/client/py-client')
        self.prefab.core.run('cd %s; pip3 install .' % client_path)
