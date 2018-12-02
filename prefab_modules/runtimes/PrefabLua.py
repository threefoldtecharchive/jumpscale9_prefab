from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabLua(base):


    NAME = "lua"

    def _init(self):
        self.BUILDDIR = self.replace("$BUILDDIR")

    def build(self, reset=True):
        """
        js_shell 'j.tools.prefab.local.runtimes.lua.build()'
        :param install:
        :return:
        """
        if self.doneCheck("build") and not reset:
            return

        #need openresty & openssl to start from
        j.tools.prefab.local.lib.openssl.build()
        j.tools.prefab.local.web.openresty.build()

        self.prefab.bash.locale_check()


        url="https://luarocks.org/releases/luarocks-3.0.4.tar.gz"
        dest = self.replace("$BUILDDIR/luarocks")
        self.prefab.core.createDir(dest)
        self.prefab.core.file_download(url, to=dest, overwrite=False, retry=3,
                    expand=True, minsizekb=100, removeTopDir=True, deletedest=True)
        C="""                
        cd $BUILDDIR/luarocks
        ./configure --prefix=/sandbox/openresty/luarocks --with-lua=/sandbox/openresty/luajit 
        make build
        make install
        luarocks install luaossl OPENSSL_DIR=/sandbox/var/build/openssl CRYPTO_DIR=/sandbox/var/build/openssl
        luarocks install luasec OPENSSL_DIR=/sandbox/var/build/openssl CRYPTO_DIR=/sandbox/var/build/openssl
        luarocks install lapis
        luarocks install moonscript
        luarocks install lapis-console
        luarocks install LuaFileSystem
        luarocks install LuaSocket 
        luarocks install lua-geoip 
        luarocks install lua-cjson
        luarocks install lua-term 
        luarocks install penlight 
        luarocks install lpeg
        luarocks install mediator_lua
        luarocks install luajwt
        # luarocks install mooncrafts
        luarocks install inspect
        luarocks install lua-resty-jwt
        luarocks install lua-resty-redis-connector
        luarocks install lua-resty-openidc

        luarocks install LuaRestyRedis
        luarocks install lua-resty-qless
        
        luarocks install lua-capnproto
        luarocks install lua-toml
        
        luarocks install lua-resty-exec
        
        luarocks install lua-resty-influx
        luarocks install lua-resty-repl


        luarocks install lua-resty-iputils

        luarocks install lsqlite3 
        
        luarocks install bcrypt
        luarocks install md5
        
        luarocks install date
        luarocks install uuid
        luarocks install lua-resty-cookie
        luarocks install lua-path
        
        #various encryption
        luarocks install luazen
        
        export LUALIB=/sandbox/openresty/lualib
        rsync -rav /sandbox/openresty/luarocks/lib/lua/5.1/ $LUALIB/
        rsync -rav /sandbox/openresty/luarocks/share/lua/5.1/ $LUALIB/
        
        #/sandbox/openresty/luajit/share/luajit-2.1.0-beta3/jit
        
           
        """
        # C = self.prefab.core.replace(C)
        C = self.replace(C)
        print(C)
        self.prefab.core.execute_bash(C)

        self.doneSet("build")


    # def build_crypto(self):
    #
    #     """
    #     # https://github.com/evanlabs/luacrypto
    #
    #     export OPENSSL_CFLAGS=-I/usr/local/opt/openssl/include/
    #     export OPENSSL_LIBS="-L/usr/local/opt/openssl/lib -lssl -lcrypto"
    #     export LUAJIT_LIB="/sandbox/openresty/luajit/lib"
    #     export LUAJIT_INC="/sandbox/openresty/luajit/include/luajit-2.1"
    #     export LUA_CFLAGS="-I/sandbox/openresty/luajit/include/luajit-2.1/"
    #     export LUA_LIB="/sandbox/openresty/luajit/lib"
    #     export LUA_INC="/sandbox/openresty/luajit/include/luajit-2.1"
    #
    #     :return:
    #     """

    def cleanup(self):
        """
        js_shell 'j.tools.prefab.local.runtimes.lua.cleanup()'
        :param install:
        :return:
        """
        C="""
        
        export LUALIB=/sandbox/openresty/lualib
        # rsync -rav /sandbox/openresty/luarocks/lib/lua/5.1/ $LUALIB/
        # rsync -rav /sandbox/openresty/luarocks/share/lua/5.1/ $LUALIB/

        set -ex
        
        rm -rf /sandbox/openresty/luajit/lib/lua
        rm -rf /sandbox/openresty/luajit/lib/luarocks
        rm -rf /sandbox/openresty/luajit/lib/pkgconfig
        rm -rf /sandbox/openresty/pod
        rm -rf /sandbox/openresty/luarocks
        rm -rf /sandbox/openresty/luajit/include
        rm -rf /sandbox/openresty/luajit/lib/lua
        rm -rf /sandbox/openresty/luajit/lib/pkgconfig
        rm -rf  /sandbox/openresty/luajit/share
        rm -rf  /sandbox/var/build
        rm -rf  /sandbox/root
        mkdir -p /sandbox/root
        
    
        """
        C = self.replace(C)
        print(C)

        self.prefab.core.execute_bash(C)


    # def package(self, name, server=''):
    #     if server:
    #         server = '--server=' + server
    #     self.prefab.core.run("luarocks install %s %s" % (server, name))
    #
    #
    #


