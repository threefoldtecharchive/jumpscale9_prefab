from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabTarantool(app):

    def _init(self):
        self.git_url = "https://github.com/tarantool/tarantool.git"
        self.tarantool_dir = self.replace("$CODEDIR/github/tarantool/tarantool")

    def install(self, reset=False, branch="1.7"):

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
            if not self.doneCheck("dependencies", reset):
                self.prefab.system.package.install("build-essential,cmake,coreutils,sed,libreadline-dev,"
                                                   "libncurses5-dev,libyaml-dev,libssl-dev,libcurl4-openssl-dev,"
                                                   "libunwind-dev,python,python-pip,python-setuptools,python-dev,"
                                                   "python-msgpack,python-yaml,python-argparse,"
                                                   "python-six,python-gevent,libicu-dev")
                requirments = 'https://raw.githubusercontent.com/tarantool/test-run/master/requirements.txt'
                download_to = "/tmp/tarantool_requirments.txt"
                self.prefab.core.file_download(requirments, to=download_to, minsizekb=1)
                cmd = "pip install -r %s" % download_to
                self.prefab.core.run(cmd, profile=True)
                self.doneSet("dependencies")

            if not self.doneCheck("tarantool", reset):
                self.prefab.tools.git.pullRepo(self.git_url, dest=self.tarantool_dir, branch=branch)
                cmd = "git submodule update --init --recursive"
                self.prefab.core.run(cmd, profile=True)
                cmd = """
                cd %s
                make clean
                rm CMakeCache.txt
                cmake -DENABLE_DIST=ON .
                make
                make install
                """ % self.tarantool_dir
                self.prefab.core.run(cmd, profile=True)
                self.doneSet("tarantool")

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

            if not self.doneCheck("msgpuck", reset):
                C = """
                set -ex
                pushd /tmp
                rm -rf msgpuck
                git clone https://github.com/rtsisyk/msgpuck.git
                cd msgpuck
                cmake .
                make
                make install
                popd
                """
                self.core.run(C)
                self.doneSet("msgpuck")

            self.prefab.system.package.install("luarocks,libsodium-dev,libb2-dev,capnproto")

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
                # luarocks install lua-avro
                popd
                """
                self.core.run(C)  
                self.doneSet("rocks2")

            if not self.doneCheck("avro", reset):
                C = """
                set -ex
                pushd /tmp
                rm -rf avro-schema
                git clone https://github.com/tarantool/avro-schema
                cd avro-schema
                cmake .
                make
                make install
                popd
                """
                self.core.run(C)
                self.doneSet("avro")

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

        #RESULT IS RUNNING TARANTOOL IN TMUX