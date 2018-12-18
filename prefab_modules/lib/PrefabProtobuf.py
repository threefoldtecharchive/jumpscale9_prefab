from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabProtobuf(app):

    NAME = "protoc"

    def install(self, reset=False):
        """
        install protobut
        """
        if self.doneCheck("install", reset):
            return

        self.prefab.system.package.mdupdate()
        if self.core.isMac:
            self.prefab.system.package.install(['protobuf'])
        else:
            url="https://github.com/google/protobuf/releases/download/v3.4.0/protoc-3.4.0-linux-x86_64.zip"
            res=self.prefab.network.tools.download(url, to='', overwrite=False, retry=3, timeout=0, expand=True,removeTopDir=False)
            self.core.file_move("%s/bin/protoc"%res,"/usr/local/bin/protoc")
        self.prefab.runtimes.pip.install(
            "protobuf3", upgrade=True)  # why not protobuf?

        self.doneSet("install")
