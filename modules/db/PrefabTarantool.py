from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabTarantool(app):

    NAME = "install"

    def install(self, reset=False):

        # if self.doneCheck("install", reset):
        #     return

        if self.core.isMac:
            # cmd="brew install tarantool"
            self.prefab.system.package.install(
                "lua,tarantool,luajit,cmake,msgpuck")

            C = """
            set -ex
            pushd $TMPDIR
            git clone http://luajit.org/git/luajit-2.0.git
            cd luajit-2.0/
            git checkout v2.1
            make && sudo make install
            ln -sf /usr/local/bin/luajit-2.1.0-beta3 /usr/local/bin/luajit
            popd

            pushd $TMPDIR
            git clone --recursive https://github.com/Sulverus/tdb
            cd tdb
            make
            sudo make install prefix=/usr//local/opt/tarantool

            sudo luarocks install redis-lua
            sudo luarocks install yaml
            sudo luarocks install penlight
            sudo luarocks install luasec OPENSSL_DIR=/usr//local/opt/openssl@1.1
            sudo tarantoolctl rocks install shard
            sudo tarantoolctl rocks install document
            sudo tarantoolctl rocks install prometheus
            sudo tarantoolctl rocks install queue
            sudo tarantoolctl rocks install expirationd
            sudo tarantoolctl rocks install connpool
            sudo tarantoolctl rocks install http
            

            # sudo luarocks install luatweetnacl

            sudo luarocks install lua-cjson

            popd
            """
            self.core.run(C)
        elif self.core.isUbuntu:

            if not self.doneCheck("apt_config", reset):
                #WRITE TARANTOOL APT CONFIG
                self.core.run("rm -f /etc/apt/sources.list.d/*tarantool*.list")
                rc,release,err=self.core.run("lsb_release -c -s")
                CONFIG="""
                deb http://download.tarantool.org/tarantool/1.7/ubuntu/ $release main
                deb-src http://download.tarantool.org/tarantool/1.7/ubuntu/ $release main
                """
                CONFIG=self.replace(CONFIG.replace("$release",release))
                self.core.file_write("/etc/apt/sources.list.d/tarantool_1_7.list",CONFIG)
                self.doneSet("apt_config")

            if not self.doneCheck("apt_parts", reset):
                self.core.run("curl http://download.tarantool.org/tarantool/1.7/gpgkey | sudo apt-key add -")
                self.prefab.system.package.mdupdate(reset=True)
                self.prefab.system.package.install("apt-transport-https,tarantool")
                self.doneSet("apt_parts")

            if not self.doneCheck("luajit", reset):
                C = """
                set -ex
                pushd /tmp
                rm -rf luajit-2.0
                git clone http://luajit.org/git/luajit-2.0.git
                cd luajit-2.0/
                git checkout v2.1
                make && sudo make install
                ln -sf /usr/local/bin/luajit-2.1.0-beta3 /usr/local/bin/luajit
                popd
                """
                self.core.run(C)  
                self.doneSet("luajit")

            if not self.doneCheck("tdb", reset):
                C = """
                set -ex
                pushd /tmp
                rm -rf tdb
                git clone --recursive https://github.com/Sulverus/tdb
                cd tdb
                make
                make install
                popd
                """
                self.core.run(C)  
                self.doneSet("tdb")

            self.prefab.system.package.install("luarocks,libsodium-dev,libb2-dev,libmsgpuck-dev")

            if not self.doneCheck("rocks1", reset):
                C = """
                set -ex
                pushd /tmp
                tarantoolctl rocks install shard
                tarantoolctl rocks install document
                tarantoolctl rocks install prometheus
                tarantoolctl rocks install queue
                tarantoolctl rocks install expirationd
                tarantoolctl rocks install connpool
                tarantoolctl rocks install http
                popd
                """
                self.core.run(C)  
                self.doneSet("rocks1")    


            if not self.doneCheck("rocks2", reset):
                C = """
                set -ex
                pushd /tmp
                luarocks install lua-capnproto
                luarocks install redis-lua
                luarocks install yaml
                luarocks install penlight
                luarocks install luasec
                luarocks install luatweetnacl
                luarocks install lua-cjson
                luarocks install luafilesystem
                luarocks install siphash --from=http://mah0x211.github.io/rocks/
                luarocks install --from=http://mah0x211.github.io/rocks/ blake2
                luarocks install symmetric
                popd
                """
                self.core.run(C)  
                self.doneSet("rocks2")                                      

        self.doneSet("install")

    def start(self, port=3301, passwd="admin007"):
        """
        """
        prefab = self.prefab

        LUA = """
        box.cfg{listen = $port}
        box.schema.user.create('admin', {if_not_exists = true,password = '$passwd'})
        box.schema.user.passwd('admin','$passwd')
        require('console').start()
        """
        LUA = LUA.replace("$passwd", passwd)
        LUA = LUA.replace("$port", str(port))

        luapath = prefab.core.replace("$TMPDIR/tarantool.lua")

        print("write lua startup to:%s" % luapath)

        prefab.core.file_write(luapath, LUA)

        cmd = "cd $TMPDIR;rm -rf tarantool;mkdir tarantool;cd tarantool;tarantool %s" % luapath
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="tarantool", cmd=cmd, env={}, path="")

        # prefab.system.tmux.createWindow("tarantool", "tarantool")

        # prefab.system.tmux.executeInScreen(
        #     "tarantool",
        #     "tarantool",
        #     "cd $TMPDIR;rm -rf tarantool;mkdir tarantool;cd tarantool;tarantool %s" %
        #     luapath,
        #     replaceArgs=True)
