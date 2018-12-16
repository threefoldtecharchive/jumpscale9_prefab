from Jumpscale import j

base = j.tools.prefab._getBaseClass()

# DANGEROUS
# HIDE OPENSSL
"""
sudo mv -f /usr/local/etc/openssl /usr/local/etc/openssl_
sudo mv -f /usr/local/Cellar/openssl /usr/local/Cellar/openssl_
sudo mv -f /usr/local/include/node/openssl /usr/local/include/node/openssl_
sudo mv -f /usr/local/include/openssl /usr/local/include/openssl_
sudo mv -f /usr/local/opt/openssl /usr/local/opt/openssl_
sudo mv -f /usr/local/ssl /usr/local/ssl_
sudo mv -f /usr/local/bin/openssl /usr/local/bin/openssl_
sudo mv -f /usr/bin/openssl /usr/bin/openssl_


 find /usr -name "*openssl*"  -exec rm -rf {} \;


"""

# UNHIDE OPENSSL
"""
sudo mv -f /usr/local/etc/openssl_ /usr/local/etc/openssl
sudo mv -f /usr/local/Cellar/openssl_ /usr/local/Cellar/openssl
sudo mv -f /usr/local/include/node/openssl_ /usr/local/include/node/openssl
sudo mv -f /usr/local/include/openssl_ /usr/local/include/openssl
sudo mv -f /usr/local/opt/openssl_ /usr/local/opt/openssl
sudo mv -f /usr/local/ssl_ /usr/local/ssl
sudo mv -f /usr/local/bin/openssl_ /usr/local/bin/openssl
sudo mv -f /usr/bin/openssl_ /usr/bin/openssl
"""


class PrefabOpenSSL(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("{DIR_VAR}/build/openssl")
        self.CODEDIRL = self.core.replace("{DIR_VAR}/build/code/openssl")

    def reset(self):
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)

    def build(self, reset=False):
        """
        js_shell 'j.tools.prefab.local.lib.openssl.build();print(j.tools.prefab.local.lib.openssl.BUILDDIRL)'
        """

        if self.doneCheck("build") and not reset:
            return
        self.prefab.system.installbase.development(python=False)
        url = "https://github.com/openssl/openssl.git"
        self.prefab.tools.git.pullRepo(url, branch="OpenSSL_1_1_0-stable",dest=self.CODEDIRL, reset=False, ssh=False)

        if not self.doneGet("compile") or reset:
            C = """
            set -ex
            mkdir -p {DIR_VAR}/build/L
            cd $CODEDIRL
            # ./config
            ./Configure $target shared enable-ec_nistp_64_gcc_128 no-ssl2 no-ssl3 no-comp --openssldir={DIR_VAR}/build/L --prefix={DIR_VAR}/build/L
            make depend
            make install
            rm -rf {DIR_VAR}/build/L/share
            rm -rf {DIR_VAR}/build/L/private
            echo "**BUILD DONE**"
            """
            if self.prefab.core.isMac:
                C = C.replace("$target", "darwin64-x86_64-cc")
            else:
                C = C.replace("$target", "linux-generic64")

            self.prefab.core.file_write("%s/mycompile_all.sh" % self.CODEDIRL, self.executor.replace(C))
            self.logger.info("compile openssl")
            self.logger.debug(C)                
            self.prefab.core.run("sh %s/mycompile_all.sh" % self.CODEDIRL)
            self.doneSet("compile")
            self.logger.info("BUILD DONE")
        else:
            self.logger.info("NO NEED TO BUILD")

        self.logger.info("BUILD COMPLETED OK")
        self.doneSet("build")
