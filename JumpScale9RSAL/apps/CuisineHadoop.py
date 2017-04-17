from JumpScale import j

base = j.tools.cuisine._getBaseClass()

# TODO: *4 unfinished but ok for now


class CuisineHadoop(base):

    def _install(self):

        if self.cuisine.core.isUbuntu:
            C = """\
            apt-get install -y apt-get install openjdk-7-jre
            cd $TMPDIR
            wget -c http://www-us.apache.org/dist/hadoop/common/hadoop-2.7.2/hadoop-2.7.2.tar.gz
            tar -xf hadoop-2.7.2.tar.gz -C /opt/
            """
            C = self.cuisine.bash.replaceEnvironInText(C)
            C = self.replace(C)
            self.cuisine.core.run(C, profile=True)
            self.cuisine.bash.addPath("/opt/hadoop-2.7.2/bin")
            self.cuisine.bash.addPath("/opt/hadoop-2.7.2/sbin")
            self.cuisine.bash.envSet("JAVA_HOME", "/usr/lib/jvm/java-7-openjdk-amd64")
            self.cuisine.bash.envSet("HADOOP_PREFIX", "/opt/hadoop-2.7.2/")
        else:
            raise NotImplementedError("unsupported platform")

    def install(self):
        self._install()
