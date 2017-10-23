from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabTarantool(app):

    NAME = "install"

    def install(self, reset=False):

        if self.doneCheck("install", reset):
            return

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
                
            sudo tarantoolctl rocks install shard
            sudo tarantoolctl rocks install document
            sudo tarantoolctl rocks install prometheus
            sudo tarantoolctl rocks install queue
            sudo tarantoolctl rocks install expirationd
            sudo tarantoolctl rocks install connpool
            sudo tarantoolctl rocks install http

            sudo luarocks install luatweetnacl

            # sudo luarocks install lua-cjson

            popd
            """
        else:
            raise RuntimeError("implement")
            # see https://github.com/Incubaid/playenv/blob/master/tarantool/install.sh

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
