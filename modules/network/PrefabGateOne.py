from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabGateOne(app):
    NAME = "gateone"

    def build(self, reset=False):
        """
        Build Gateone
        :param reset: reset build if already built before
        :return:
        """
        if self.doneCheck("build", reset):
            return

        self.prefab.tools.git.pullRepo("https://github.com/liftoff/GateOne", branch="master")

        self.doneSet('build')

    def install(self, reset=False):
        """
        Installs gateone

        @param reset: boolean: forces the install operation.
    
        """
        if reset is False and self.isInstalled():
            return

        cmd = """
cd /opt/code/github/liftoff/GateOne
apt-get install build-essential python3-dev python3-setuptools -y
python3 setup.py install
cp /usr/local/bin/gateone $BINDIR/gateone
"""
        self.prefab.core.run(cmd)

        self.doneSet('install')

    def start(self, name="main", address="localhost", port=10443):

        """
        Starts gateone.

        @param name: str: instance name.
        @param address: str: bind address.
        @param port: int: port number.

        """

        cmd = "gateone --address={} --port={} --disable_ssl".format(address, port)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name='gateone_{}'.format(name), cmd=cmd)

    def stop(self, name='main'):
        """
        Stops gateone 
        """
        pm = self.prefab.system.processmanager.get()
        pm.stop(name='gateone_{}'.format(name))

    def restart(self, name="main"):
        """
        Restart GateOne instance by name.
        """
        self.stop(name)
        self.start(name)

    def reset(self):
        """
        helper method to clean what this module generates.
        """
        pass
