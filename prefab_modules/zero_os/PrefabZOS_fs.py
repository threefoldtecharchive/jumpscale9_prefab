from Jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabZOS_fs(app):
    """
    fuse based filesystem for our g8OS, but can be used in other context too
    """
    NAME = 'fs'

    def build(self, start=False, install=True, reset=False):
        if reset is False and self.isInstalled():
            return

        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install('build-essential')

        self.prefab.runtimes.golang.get("github.com/g8os/fs")
        self.prefab.core.file_copy("{DIR_BASE}/go/bin/fs", "{DIR_BASE}/bin/")

        if install:
            self.install(start)

    def install(self, start=False):
        """
        download, install, move files to appropriate places, and create relevant configs
        """
        content = """
        [[mount]]
            path="/opt"
            flist="/optvar/cfg/fs/js8_opt.flist"
            backend="opt"
            mode="RO"
            trim_base=true
        [backend]
        [backend.opt]
            path="/optvar/fs_backend/opt"
            stor="public"
            namespace="js8_opt"
            cleanup_cron="@every 1h"
            cleanup_older_than=24
            log=""
        [aydostor]
        [aydostor.public]
            addr="http://stor.jumpscale.org/storx"
            login=""
            passwd=""
        """
        self.prefab.core.dir_ensure("$TEMPLATEDIR/cfg/fs")
        self.prefab.core.file_copy("{DIR_BASE}/go/bin/fs", "{DIR_BASE}/bin")
        self.prefab.core.file_write("{DIR_BASE}/go/src/github.com/g8os/fs/config/config.toml", content)
        self.prefab.core.file_copy("{DIR_BASE}/go/src/github.com/g8os/fs/config/config.toml", "$TEMPLATEDIR/cfg/fs")
        self.prefab.core.file_download(
            "https://stor.jumpscale.org/storx/static/js8_opt.flist", "$TEMPLATEDIR/cfg/fs/js8_opt.flist", minsizekb=0)
        if start:
            self.start()

    def start(self):
        self.prefab.core.file_copy("$TEMPLATEDIR/cfg/fs", "{DIR_BASE}/cfg", recursive=True)
        pm = self.prefab.system.processmanager.get()
        pm.ensure('fs', cmd="{DIR_BIN}/fs -c {DIR_BASE}/cfg/fs/config.toml")
