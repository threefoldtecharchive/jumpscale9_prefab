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
            # self.prefab.system.package.install(
            #     "lua,tarantool,luajit,cmake,msgpuck")

            #NEED TO INSTALL RIGHT TARANTOOL

            C = """
            set -ex


            curl http://download.tarantool.org/tarantool/1.7/gpgkey | sudo apt-key add -
            release=`lsb_release -c -s`

            # install https download transport for APT
            apt-get -y install apt-transport-https

            # append two lines to a list of source repositories
            rm -f /etc/apt/sources.list.d/*tarantool*.list
            tee /etc/apt/sources.list.d/tarantool_1_7.list <<- EOF
            deb http://download.tarantool.org/tarantool/1.7/ubuntu/ $release main
            deb-src http://download.tarantool.org/tarantool/1.7/ubuntu/ $release main
            EOF

            # install
            apt-get update
            apt-get -y install tarantool

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
            make install prefix=/usr/lib/tarantool/

            tarantoolctl rocks install shard
            tarantoolctl rocks install document
            tarantoolctl rocks install prometheus
            tarantoolctl rocks install queue
            tarantoolctl rocks install expirationd
            tarantoolctl rocks install connpool
            tarantoolctl rocks install http

            luarocks install redis-lua
            luarocks install yaml
            luarocks install penlight
            luarocks install luasec OPENSSL_DIR=/usr//local/opt/openssl@1.1
            luarocks install luatweetnacl
            luarocks install lua-cjson

            #NEED TARANTOOL INSTALL

            popd
            """
            self.core.run(C)            
            raise RuntimeError("implement")

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
