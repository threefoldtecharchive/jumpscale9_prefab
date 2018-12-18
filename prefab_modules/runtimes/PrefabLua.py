from Jumpscale import j

base = j.tools.prefab._BaseClass


class PrefabLua(base):


    NAME = "lua"

    def _init(self):
        self.BUILDDIR = self.executor.replace("{DIR_VAR}/build/")

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
        dest = self.executor.replace("{DIR_VAR}/build/luarocks")
        self.prefab.core.createDir(dest)
        self.prefab.core.file_download(url, to=dest, overwrite=False, retry=3,
                    expand=True, minsizekb=100, removeTopDir=True, deletedest=True)
        C="""                
        cd {DIR_VAR}/build/luarocks
        ./configure --prefix=/sandbox/openresty/luarocks --with-lua=/sandbox/openresty/luajit 
        make build
        make install
        
        cp /sandbox/var/build/luarocks/luarocks /sandbox/bin/luarocks
        
        """

        self.prefab.core.execute_bash(self.executor.replace(C))

        self.lua_rocks_install()
        self.copy2sandbox_github()

        self.doneSet("build")


    def lua_rock_install(self,name,reset=False):

        if self.doneCheck("lua_rock_install_%s"%name) and not reset:
            return

        C = "source /sandbox/env.sh;luarocks install $NAME OPENSSL_DIR=/sandbox/var/build/openssl CRYPTO_DIR=/sandbox/var/build/openssl"
        C = C.replace("$NAME",name)
        self.prefab.core.run(self.executor.replace(C))

        self.doneSet("lua_rock_install_%s"%name)


    def lua_rocks_install(self,reset=False):
        """
        js_shell 'j.tools.prefab.local.runtimes.lua.lua_rocks_install()'
        :param install:
        :return:
        """

        if self.prefab.core.isUbuntu:
            # self.prefab.system.package.mdupdate()
            self.prefab.system.package.install("geoip-database,libgeoip-dev")

        C="""
        luaossl
        luasec 
        lapis
        moonscript
        lapis-console
        LuaFileSystem
        LuaSocket 
        lua-geoip 
        lua-cjson
        lua-term 
        penlight 
        lpeg
        mediator_lua
        # luajwt
        # mooncrafts
        inspect
        lua-resty-jwt
        lua-resty-redis-connector
        lua-resty-openidc

        LuaRestyRedis
        lua-resty-qless
        
        lua-capnproto
        lua-toml
        
        lua-resty-exec
        
        lua-resty-influx
        lua-resty-repl


        lua-resty-iputils

        lsqlite3 
        
        bcrypt
        md5
        
        date
        uuid
        lua-resty-cookie
        lua-path
        
        #various encryption
        luazen
        """

        for line in C.split("\n"):
            line = line.strip()
            if line == "":
                continue
            if line.startswith("#"):
                continue
            self.lua_rock_install(line)


        C="""
        export LUALIB=/sandbox/openresty/lualib
        rsync -rav /sandbox/var/build/luarocks/lua_modules/lib/lua/5.1/ $LUALIB/
        rsync -rav /sandbox/var/build/luarocks/lua_modules/share/lua/5.1/ $LUALIB/

        """
        self.prefab.core.execute_bash(self.executor.replace(C))



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
        C = self.executor.replace(C)
        print(C)

        self.prefab.core.execute_bash(C)


    def copy2sandbox_github(self):
        """
        js_shell 'j.tools.prefab.local.runtimes.lua.copy2sandbox_github()'
        :return:
        """
        assert self.executor.type=="local"
        path="/sandbox/openresty/lualib"

        if self.core.isUbuntu:
            destbin="%s/base/openresty/lualib"%j.clients.git.getContentPathFromURLorPath("git@github.com:threefoldtech/sandbox_ubuntu.git")
        elif self.core.isMac:
            destbin="%s/base/openresty/lualib"%j.clients.git.getContentPathFromURLorPath("git@github.com:threefoldtech/sandbox_osx.git")
        else:
            raise RuntimeError("only ubuntu & osx support")

        dest="%s/base/openresty/lualib"%j.clients.git.getContentPathFromURLorPath("git@github.com:threefoldtech/sandbox_base.git")

        for item in j.sal.fs.listFilesInDir(path, recursive=True):
            rdest = j.sal.fs.pathRemoveDirPart(item,path)
            if j.sal.fs.getFileExtension(item)=="so":
                d2=destbin
            elif j.sal.fs.getFileExtension(item)=="lua":
                d2=dest
            else:
                raise RuntimeError(item)
            dir_dest_full=j.sal.fs.getDirName(j.sal.fs.joinPaths(d2,rdest))
            j.sal.fs.createDir(dir_dest_full)
            dest_full=j.sal.fs.joinPaths(d2,rdest)
            print("copy: %s %s"%(item,dest_full))
            j.sal.fs.copyFile(item,dest_full)



        self.cleanup()


