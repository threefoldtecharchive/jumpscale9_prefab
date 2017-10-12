from js9 import j
import os
import textwrap

app = j.tools.prefab._getBaseAppClass()

# TODO: *1 needs to be tested prob


class PrefabMicroEditor(app):
    NAME = "micro"

    # def _init(self):
    #     self._gogspath = str()
    #     self._gopath = str()
    #     self._appini = str()
    #     self.BUILDDIR = self.replace("$BUILDDIR/caddy")
    #     self.GOGSPATH = self.replace("$GOPATH/src/github.com/gogits/gogs")
    #     self.CODEDIR = self.GOGSPATH
    #     self.INIPATH = self.replace("$GOGSPATH/custom/conf/app.ini")

    # @property
    # def GOPATH(self):
    #     return self.prefab.runtimes.golang.GOPATH


    # def build(self, install=True, start=True, reset=False, installDeps=False):

    #     if self.doneGet('build') and not reset:
    #         return

    #     self.prefab.runtimes.golang.install()
    #     self.prefab.runtimes.golang.glide()

    #     self.prefab.bash.envSet('GOGITSDIR', '%s/src/github.com/gogits' % self.GOGSPATH)
    #     self.prefab.bash.envSet('GOGSDIR', '$GOGITSDIR/gogs')

    #     self.prefab.runtimes.golang.get('golang.org/x/oauth2')
    #     self.prefab.runtimes.golang.get('github.com/gogits/gogs')

    #     self.prefab.core.run('cd %s && git remote add gigforks https://github.com/gigforks/gogs' % self.GOGSPATH,
    #                           profile=True)
    #     self.prefab.core.run('cd %s && git fetch gigforks && git checkout gigforks/itsyouimpl' % self.GOGSPATH,
    #                           profile=True, timeout=1200)
    #     self.prefab.core.run('cd %s && glide install && go build -tags "sqlite cert"' % self.GOGSPATH, profile=True,
    #                           timeout=1200)

    #     self.doneSet('build')

    def install(self):
        """
        GOGS has no files to move this method is for standardization of prefab
        """
        if self.core.isMac:
            url = "https://github.com/zyedidia/micro/releases/download/nightly/micro-1.3.4-dev.17-osx.tar.gz"
        elif self.core.isUbuntu:
            url = "https://github.com/zyedidia/micro/releases/download/nightly/micro-1.3.4-dev.17-linux64.tar.gz"
        else:
            raise RuntimeError("not implemented for other platforms")
        
        dest=j.tools.prefab.local.network.tools.download(url=url, to='$TMPDIR/micro/', overwrite=False, retry=3, expand=True,removeTopDir=True)
        self.core.file_move("$TMPDIR/micro/micro", "/usr/local/bin/micro", recursive=False)
