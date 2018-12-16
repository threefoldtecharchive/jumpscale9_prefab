from Jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabIPFS(app):
    NAME = "ipfs"

    def isInstalled(self):
        """
        Checks if a package is installed or not
        You can ovveride it to use another way for checking
        """
        return self.prefab.core.file_exists('{DIR_BIN}/ipfs')

    def install(self, name='main', reset=False):
        if reset is False and self.isInstalled():
            return

        if self.prefab.platformtype.isLinux:
            url = "https://dist.ipfs.io/go-ipfs/v0.4.4/go-ipfs_v0.4.4_linux-amd64.tar.gz"
        elif "darwin" in self.prefab.platformtype.osname:
            url = "https://dist.ipfs.io/go-ipfs/v0.4.4/go-ipfs_v0.4.4_darwin-amd64.tar.gz"

        name = url.split('/')[-1]
        compress_path = self.executor.replace('{DIR_TEMP}/{}'.format(name))
        self.prefab.core.file_download(url, compress_path)

        uncompress_path = self.executor.replace('{DIR_TEMP}/go-ipfs')
        if self.prefab.core.file_exists(uncompress_path):
            self.prefab.core.dir_remove(uncompress_path)

        self.prefab.core.run("cd {DIR_TEMP}; tar xvf {}".format(name))
        self.prefab.core.file_copy('{}/ipfs'.format(uncompress_path), '{DIR_BIN}/ipfs')

    def uninstall(self):
        """
        remove ipfs binary from {DIR_BIN}
        """
        if self.prefab.core.file_exists('{DIR_BIN}/ipfs'):
            self.prefab.core.file_unlink('{DIR_BIN}/ipfs')

    def start(self, name='main', readonly=False):
        cfg_dir = '{DIR_BASE}/cfg/ipfs/{}'.format(name)
        if not self.prefab.core.file_exists(cfg_dir):
            self.prefab.core.dir_ensure(cfg_dir)

        # check if the ipfs repo has not been created yet.
        if not self.prefab.core.file_exists(cfg_dir + '/config'):
            cmd = 'IPFS_PATH={} {DIR_BIN}/ipfs init'.format(cfg_dir)
            self.prefab.core.run(cmd)

        cmd = '{DIR_BIN}/ipfs daemon'
        if not readonly:
            cmd += '  --writable'

        pm = self.prefab.system.processmanager.get()
        pm.ensure(
            name='ipfs_{}'.format(name),
            cmd=cmd,
            path=cfg_dir,
            env={'IPFS_PATH': cfg_dir}
        )

    def stop(self, name='main'):
        pm = self.prefab.system.processmanager.get()
        pm.stop(name='ipfs_{}'.format(name))
