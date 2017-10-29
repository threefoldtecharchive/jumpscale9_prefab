from js9 import j
import os
import textwrap

app = j.tools.prefab._getBaseAppClass()


class PrefabTendermint(app):
    NAME = "tendermint"

    def _init(self):
        self.BUILDDIR = self.replace("$BUILDDIR/tendermint")

    @property
    def TENDERMINTPATH(self):
        return "{}/src/github.com/tendermint/tendermint".format(self.prefab.runtimes.golang.GOPATH)

    def build(self, reset=False):
        """
        Builds tendermint

        @param reset boolean: forces the build operation.
        """
        if self.doneCheck("build", reset):
            return

        self.prefab.runtimes.golang.install()
        self.prefab.runtimes.golang.glide()

        self.prefab.runtimes.golang.get(
            'github.com/tendermint/tendermint/cmd/tendermint')
        self.prefab.core.run("cd {TENDERMINTPATH} && glide install".format(
            TENDERMINTPATH=self.TENDERMINTPATH))

        self.doneSet('build')

    def install(self, reset=False):
        """
        Installs tendermint

        @param reset boolean: forces the install operation.
        """
        if reset is False and self.isInstalled():
            return
        self.prefab.core.run("cd {TENDERMINTPATH} && go install ./cmd/tendermint && tendermint init".format(
            TENDERMINTPATH=self.TENDERMINTPATH))

        self.doneSet('install')

    def start_one_node(self, name="main", proxy_app="dummy"):
        """
        Starts one node.

        @param name str="main" : process name used in the processmanager.
        @param proxy_app str="dummy": proxy_app used when starting node.
        """
        cmd = "tendermint node --proxy_app={}".format(
            proxy_app)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='tendermint_{}'.format(name), cmd=cmd)

    def start(self, name='main'):
        """
        Starts tendermint.
        """
        self.start_one_node()

    def stop(self, name='main'):
        """
        Stops tendermint 
        """

        # FIXME: https://github.com/Jumpscale/prefab9/issues/61 (process
        # doesn't get killed only the pane.)
        # use self.stop_all for now
        pm = self.prefab.system.processmanager.get()
        pm.stop(name='tendermint_{}'.format(name))

    def stop_all(self):
        """
        Force stop all tendermint processes
        """
        self.prefab.system.process.kill("tendermint")

    def restart(self, name="main"):
        self.stop(name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        pass

    def test(self):
        self.build()
        self.install()
        self.start('test')
        self.stop_all()
        self.start('test')
