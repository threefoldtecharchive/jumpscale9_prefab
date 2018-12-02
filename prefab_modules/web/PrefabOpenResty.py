from Jumpscale import j
import os
import textwrap
from time import sleep


app = j.tools.prefab._getBaseAppClass()


class PrefabOpenResty(app):
    NAME = 'openresty'

    def _init(self):
        self.BUILDDIR = self.replace("$BUILDDIR")


    def install(self, start=True):
        """
        Moving build files to build directory and copying config files
        """

        """
        # Install through ubuntu
        # self.prefab.system.package.mdupdate()
        # self.prefab.system.package.ensure('openresty')
        # link openresty to binDir and use it from there

        # self.prefab.core.dir_ensure("$JSAPPSDIR/openresty/")
        # self.prefab.core.dir_ensure("$JSAPPSDIR/openresty/bin")
        # self.prefab.core.dir_ensure("$JSAPPSDIR/openresty/etc")
        self.prefab.core.dir_ensure("$JSCFGDIR")
        self.prefab.core.dir_ensure("$TMPDIR")
        # self.prefab.core.dir_ensure("/optvar/tmp")
        self.prefab.core.dir_ensure("$JSAPPSDIR/openresty/")
        self.prefab.core.dir_ensure("$JSAPPSDIR/openresty/bin")
        self.prefab.core.dir_ensure("$JSAPPSDIR/openresty/etc")
        self.prefab.core.dir_ensure("$JSCFGDIR/openresty/etc")

        self.prefab.core.file_copy('/usr/sbin/openresty', '$JSAPPSDIR/openresty/bin/openresty', overwrite=True)
        self.prefab.core.dir_ensure('/var/log/openresty')
        self.prefab.core.file_copy('/etc/openresty/*', '$JSAPPSDIR/openresty/etc/', recursive=True)  # default conf
        self.prefab.core.file_copy('/etc/openresty/*', '$JSCFGDIR/openresty/etc/', recursive=True)  # variable conf
        """

        # Install openresty

        C = """
        #!/bin/bash
        set -ex

        cd $TMPDIR/build/openresty/openresty-1.11.3
        make install
        """

        C = self.prefab.core.replace(C)
        C = self.replace(C)
        self.prefab.core.run(C)

        # Writing config files
        self.prefab.core.dir_ensure("$BUILDDIR/openresty/conf/conf.d/")
        self.prefab.core.dir_ensure("$BUILDDIR/openresty/conf/sites-enabled/")

        basicopenrestyconf = self.get_basic_openresty_conf()
        basicopenrestyconf = self.replace(textwrap.dedent(basicopenrestyconf))

        defaultenabledsitesconf = self.get_basic_openresty_site()
        defaultenabledsitesconf = self.replace(textwrap.dedent(defaultenabledsitesconf))

        self.prefab.core.file_write("$BUILDDIR/openresty/conf/openresty.conf", content=basicopenrestyconf)
        self.prefab.core.file_write("$BUILDDIR/openresty/conf/sites-enabled/default", content=defaultenabledsitesconf)

        fst_cgi_conf = self.prefab.core.file_read("$BUILDDIR/openresty/conf/fastcgi.conf")
        fst_cgi_conf = fst_cgi_conf.replace("include fastcgi.conf;",
                                            self.replace("include $BUILDDIR/openresty/conf/fastcgi.conf;"))
        self.prefab.core.file_write("$BUILDDIR/openresty/conf/fastcgi.conf", content=fst_cgi_conf)

        #self.prefab.core.file_link(source="$JSCFGDIR/openresty", destination="$JSAPPSDIR/openresty")
        if start:
            self.start()

    def build(self, reset=False):
        """
        js_shell 'j.tools.prefab.local.web.openresty.build()'
        :param install:
        :return:
        """
        if self.doneCheck("build") and not reset:
            return

        self.prefab.bash.locale_check()

        if self.prefab.core.isUbuntu:
            self.prefab.system.package.mdupdate()
            self.prefab.system.package.install("build-essential libpcre3-dev libssl-dev")

            self.prefab.core.dir_remove("$TMPDIR/build/openresty")
            self.prefab.core.dir_ensure("$TMPDIR/build/openresty")

            C = """
            #!/bin/bash
            set -ex

            cd $TMPDIR/build/openresty
            wget http://openresty.org/download/openresty-1.11.3.tar.gz
            tar xzf openresty-1.11.3.tar.gz

            cd openresty-1.11.3
            ./configure --prefix=$BUILDDIR/openresty/ --with-http_ssl_module --with-ipv6
            make
            """
            C = self.prefab.core.replace(C)
            C = self.replace(C)
            self.prefab.core.run(C)

        else:
            #build with system openssl, no need to include custom build
            # j.tools.prefab.local.lib.openssl.build()

            url="https://openresty.org/download/openresty-1.13.6.2.tar.gz"
            dest = self.replace("$BUILDDIR/openresty")
            self.prefab.core.createDir(dest)
            self.prefab.core.file_download(url, to=dest, overwrite=False, retry=3,
                        expand=True, minsizekb=1000, removeTopDir=True, deletedest=True)
            C="""
            cd $BUILDDIR/openresty
            mkdir -p /sandbox/var/pid
            mkdir -p /sandbox/var/log
            ./configure \
                --with-cc-opt="-I/usr/local/opt/openssl/include/ -I/usr/local/opt/pcre/include/" \
                --with-ld-opt="-L/usr/local/opt/openssl/lib/ -L/usr/local/opt/pcre/lib/" \
                --prefix="/sandbox/openresty" \
                --sbin-path="/sandbox/bin/openresty" \
                --modules-path="/sandbox/lib" \
                --pid-path="/sandbox/var/pid/openresty.pid" \
                --error-log-path="/sandbox/var/log/openresty.log" \
                --lock-path="/sandbox/var/nginx.lock" \
                --conf-path="/sandbox/cfg/openresty.cfg" \
                -j8
            make -j8
            make install
            rm -rf $BUILDDIR/openresty
            
            ln -s /sandbox/openresty/luajit/bin/luajit /sandbox/bin/lua
            
            """
            C = self.prefab.core.replace(C)
            C = self.replace(C)
            self.prefab.core.run(C)

        self.doneSet("build")




    def test(self):
        # host a file test can be reached
        raise NotImplementedError
