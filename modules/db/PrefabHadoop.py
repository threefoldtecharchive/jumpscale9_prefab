from js9 import j

base = j.tools.prefab._getBaseClass()

# TODO: *4 unfinished but ok for now


class PrefabHadoop(base):

    def _install(self):

        if self.prefab.core.isUbuntu:
            C = """\
            apt-get install -y apt-get install openjdk-7-jre
            cd $TMPDIR
            wget -c http://www-us.apache.org/dist/hadoop/common/hadoop-2.7.2/hadoop-2.7.2.tar.gz
            tar -xf hadoop-2.7.2.tar.gz -C /opt/
            """
            C = self.prefab.core.replace(C)
            C = self.replace(C)
            self.prefab.core.run(C, profile=True)
            self.prefab.bash.addPath("/opt/hadoop-2.7.2/bin")
            self.prefab.bash.addPath("/opt/hadoop-2.7.2/sbin")
            self.prefab.bash.envSet("JAVA_HOME", "/usr/lib/jvm/java-7-openjdk-amd64")
            self.prefab.bash.envSet("HADOOP_PREFIX", "/opt/hadoop-2.7.2/")
        else:
            raise NotImplementedError("unsupported platform")

    def install(self):
        self._install()
