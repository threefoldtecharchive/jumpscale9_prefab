from Jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabJumpscaleCore(app):
    NAME = 'jumpscale'

    def install(self, reset=False, branch='development_960', full=False):
        """Install jumpscale core
        Keyword Arguments:
            reset {bool} -- force install if jumpscalecore was already installed (default: {False})
            branch {string} -- branch from which jumpscalecore will be installed (default: {'master'})
            full {bool} -- False for production installs and True for development installs
        Example:
            j.tools.prefab.local.jumpscale.jumpscaleCore.install()

            or from bash

            js_prefab local 'jumpscale.jumpscalecore.install(reset=True)'
        """
        if self.doneCheck("install", reset):
            return

        if full:
            self.prefab.system.installbase.development()
        else:
            self.prefab.system.installbase.install()

        self.prefab.runtimes.pip.ensure()

        S = """
        echo "INSTALL JUMPSCALE"
        curl https://raw.githubusercontent.com/threefoldtech/jumpscale_core/{}/install.sh?$RANDOM > /tmp/install_jumpscale.sh
        bash /tmp/install_jumpscale.sh
        """.format(branch)

        env = None
        if full:
            env = {'JSFULL': '1'}
        self.core.execute_bash(S, env=env)

        assert self.core.run("js_shell 'j.tools.console.echo(\"1\")'")[1] == '1'

        self.logger.info("jumpscale_install")

        self.doneSet("install")
