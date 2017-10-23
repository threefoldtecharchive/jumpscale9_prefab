from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabProtobuf(app):

    NAME = "protoc"

    def install(self, reset=False):
        """
        install protobut
        """
        if self.doneCheck("install", reset):
            return

        self.prefab.system.package.mdupdate()
        self.prefab.system.package.multiInstall(['protobuf'])
        self.prefab.runtimes.pip.install(
            "protobuf3", upgrade=True)  # why not protobuf?

        self.doneSet("install")
