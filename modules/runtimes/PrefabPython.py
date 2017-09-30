from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabPython(base):

    def _init(self):
        self.BUILDDIRL = self.core.replace("$BUILDDIR/python3/")
        self.CODEDIRL = self.core.replace("$CODEDIR/github/python/cpython/")

    def reset(self):
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)
        self.prefab.development.pip.reset()

    def build(self, reset=False):
        """
        """

        if reset:
            self.reset()

        if self.doneGet("build") and not reset:
            self.pipAll()
            return

        self.prefab.development.openssl.build()
        self.prefab.development.libffi.build()
        self.prefab.package.install('zlib1g-dev')
        if self.prefab.core.isMac:
            if not self.doneGet("xcode_install"):
                self.prefab.core.run("xcode-select --install", die=False, showout=True)
                C = """
                openssl
                xz
                """
                self.prefab.package.multiInstall(C)
                self.doneSet("xcode_install")

        if not self.doneGet("compile") or reset:
            cpath = self.prefab.development.git.pullRepo(
                'https://github.com/python/cpython', branch="3.6", reset=reset)
            assert cpath.rstrip("/") == self.CODEDIRL.rstrip("/")
            if self.core.isMac:  # TODO: *2 cant we do something similar for linux?

                C = """
                set -ex
                cd $CODEDIRL

                export LIBRARY_PATH="$openssldir/lib:$libffidir/lib"
                export CPPPATH="$openssldir/include"
                export CPATH="$openssldir/include"
                export PATH=$openssldir/lib:/$openssldir/bin:/usr/local/bin:/usr/bin:/bin

                export CFLAGS="-I$CPATH/"
                export CPPFLAGS="-I$CPATH/"
                export LDFLAGS="-L$LIBRARY_PATH/"

                echo $CFLAGS
                echo $LDFLAGS

                ./configure
                make -s -j4


                """

                C = C.replace("$openssldir", self.prefab.development.openssl.BUILDDIRL)
                C = C.replace("$libffidir", self.prefab.development.libffi.BUILDDIRL)
                C = self.replace(C)

                self.prefab.core.file_write("%s/mycompile_all.sh" % self.CODEDIRL, C)
            else:  # TODO: *1 not working compile, see if we can do in line with osx, something wrong with openssl
                # configure custom location for openssl
                setup_path = '{}/Modules/Setup'.format(self.CODEDIRL)
                self.prefab.core.file_copy(setup_path + ".dist", setup_path)
                content = """
                    _socket socketmodule.c
                    SSL={openssldir}
                    _ssl _ssl.c -DUSE_SSL -I$(SSL)/include -I$(SSL)/include/openssl -L$(SSL)/lib -lssl -lcrypto
                    """.format(openssldir=self.prefab.development.openssl.BUILDDIRL)

                self.prefab.core.file_write(location=setup_path, content=content, append=True)

                C = """
                set -ex
                cd {codedir}

                ./configure --prefix={builddir}

                export LD_LIBRARY_PATH={openssldir}/lib
                make clean
                make -j4
                make install
                """.format(builddir=self.BUILDDIRL, codedir=self.CODEDIRL, openssldir=self.prefab.development.openssl.BUILDDIRL)

            self.logger.info("compile python3")
            self.logger.info(C)
            self.prefab.core.run(C)

        self.doneSet("compile")

        # find buildpath for lib (depending source it can be other destination)
        # is the core python binaries
        libBuildName = [item for item in self.prefab.core.run(
            "ls %s/build" % self.CODEDIRL)[1].split("\n") if item.startswith("lib")][0]
        lpath = j.sal.fs.joinPaths(self.CODEDIRL, "build", libBuildName)
        self.prefab.core.copyTree(source=lpath, dest=self.BUILDDIRL, keepsymlinks=True, deletefirst=False,
                                   overwriteFiles=True, recursive=True, rsyncdelete=False, createdir=True)

        # copy python libs (non compiled)
        ignoredir = ["tkinter", "turtledemo",
                     "msilib", "pydoc*", "lib2to3", "idlelib"]
        lpath = self.replace("$CODEDIRL/Lib")
        ldest = self.replace("$BUILDDIRL/plib")
        self.prefab.core.copyTree(source=lpath, dest=ldest, keepsymlinks=True, deletefirst=False,
                                   overwriteFiles=True, ignoredir=ignoredir,
                                   recursive=True, rsyncdelete=True, createdir=True)

        self.prefab.core.file_unlink("%s/python3" % self.BUILDDIRL)
        if self.core.isMac:
            self.prefab.core.file_copy("%s/python.exe" % self.CODEDIRL, "%s/python3" % self.BUILDDIRL)
        else:
            self.prefab.core.file_copy("%s/python" % self.CODEDIRL, "%s/python3" % self.BUILDDIRL)

        C = """
            cd $BUILDDIRL
            mkdir -p bin
            rm -f bin/python3
            mv python3 bin/python3
            ln -s bin/python3 python3
        """
        self.prefab.core.run(self.replace(C))

        # copy includes
        lpath = j.sal.fs.joinPaths(self.CODEDIRL, "Include",)
        ldest = j.sal.fs.joinPaths(self.BUILDDIRL, "include/python")
        self.prefab.core.copyTree(source=lpath, dest=ldest, keepsymlinks=True, deletefirst=False,
                                   overwriteFiles=True, ignoredir=ignoredir,
                                   recursive=True, rsyncdelete=False, createdir=True)

        # now copy openssl parts in
        self.prefab.core.copyTree(source=self.prefab.development.openssl.BUILDDIRL, dest=self.BUILDDIRL,
                                   keepsymlinks=True, deletefirst=False,
                                   overwriteFiles=True, ignoredir=ignoredir,
                                   recursive=True, rsyncdelete=False, createdir=True)

        self.prefab.core.file_copy("%s/pyconfig.h" % self.CODEDIRL, "%s/include/python/pyconfig.h" % self.BUILDDIRL)
        C = """

        export JSBASE=`pwd`

        export PATH=$JSBASE:$JSBASE/bin:$JSBASE/lib/$JSPATH:/usr/local/bin:/usr/bin:/bin

        #export LUA_PATH="/opt/jumpscale9/lib/lua/?.lua;./?.lua;/opt/jumpscale9/lib/lua/?/?.lua;/opt/jumpscale9/lib/lua/tarantool/?.lua;/opt/jumpscale9/lib/lua/?/init.lua"

        export PYTHONPATH=$JSBASE/plib:$JSBASE/plib.zip:$JSBASE:$JSBASE/lib:$JSBASE/plib/site-packages:$JSBASE/lib/python3.6/site-packages
        export PYTHONHOME=$JSBASE
        export CPATH=$JSBASE/include:$JSBASE/include/openssl:$JSBASE/lib:$JSBASE/include/python

        export LC_ALL=en_US.UTF-8
        export LANG=en_US.UTF-8

        export LD_LIBRARY_PATH=$JSBASE/bin:$JSBASE/lib
        export PS1="JS8: "
        if [ -n "$BASH" -o -n "$ZSH_VERSION" ] ; then
                hash -r 2>/dev/null
        fi
        """.format(JSBASE=j.dirs.JSBASEDIR)

        self.prefab.core.file_write("%s/env.sh" % self.BUILDDIRL, C, replaceArgs=True)

        if not self.doneGet("pip3install") or reset:
            C = """
            set -ex
            cd $BUILDDIRL
            source env.sh
            rm -rf get-pip.py
            curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
            $BUILDDIRL/bin/python3 get-pip.py
            """
            self.prefab.core.run(self.replace(C))
        self.doneSet("pip3install")

        self.prefab.package.ensure("libssl-dev")
        self.prefab.package.ensure("libcapnp-dev")
        self.pipAll()

        msg = "\n\nto test do:\ncd $BUILDDIRL;source env.sh;python3"
        msg = self.replace(msg)
        self.logger.info(msg)
        self.doneSet("build")

    def sandbox(self, reset=False, deps=True):
        if deps:
            self.build(reset=reset)
        if self.doneGet("sandbox") and not reset:
            return

        C = """
        set -ex
        cd $BUILDDIRL

        rm -rf share
        mkdir -p lib/python3.6/site-packages/
        rsync -rav lib/python3.6/site-packages/ plib/site-packages/
        rm -rf lib/python3.6
        find . -name '*.pyc' -delete

        find . -name 'get-pip.py' -delete
        set +ex
        find -L .  -name '__pycache__' -exec rm -rf {} \;
        find . -name "*.dist-info" -exec rm -rf {} \;
        find . -name "*.so" -exec mv {} lib/ \;

        # rm -f _sysconfigdata_m_darwin_darwin.py
        rm -f openssl*

        """
        self.prefab.core.run(self.replace(C))

        # now copy jumpscale in
        linkpath = "%s/lib/JumpScale" % self.prefab.core.dir_paths["JSBASEDIR"]
        C = "ln -s %s %s/lib/JumpScale" % (linkpath, self.BUILDDIRL)
        if not self.prefab.core.file_exists("%s/lib/JumpScale" % self.BUILDDIRL):
            self.core.run('rm -rf %s/lib/JumpScale' % self.BUILDDIRL)
            self.prefab.core.run(C)

        # # now create packaged dir
        # destpath2 = self.BUILDDIRL.rstrip("/").rstrip() + "2"
        # self.prefab.core.copyTree(source=self.BUILDDIRL, dest=destpath2, keepsymlinks=False, deletefirst=True,
        #                            overwriteFiles=True,
        #                            recursive=True, rsyncdelete=True, createdir=True)

        # zip trick does not work yet lets leave for now
        # C = """
        # set -ex
        # cd %s/plib
        # zip -r ../plib.zip *
        # cd ..
        # rm -rf plib
        # """ % destpath2
        # self.prefab.core.run(C)

        # self.doneSet("sandbox")

    def pipAll(self, reset=False):
        # needs at least items from /JS8/code/github/jumpscale/jumpscale_core9/install/dependencies.py
        C = """
        uvloop
        redis
        paramiko
        watchdog
        gitpython
        click
        pymux
        pyyaml
        ipdb
        requests
        netaddr
        ipython
        cython
        pycapnp
        path.py
        colored-traceback
        pudb
        colorlog
        msgpack-python
        pyblake2
        brotli
        pysodium
        ipfsapi
        curio
        uvloop
        gevent
        """
        self.prefab.package.multiInstall(['libffi-dev', 'libssl-dev'])
        self.pip(C, reset=reset)
        self.sandbox(deps=False)

    def pip(self, pips, reset=False):
        for item in pips.split("\n"):
            item = item.strip()
            if item == "":
                continue
            # cannot use prefab functionality because would not be sandboxed
            if not self.doneGet("pip3_%s" % item) or reset:
                C = "set -ex;cd $BUILDDIRL;source env.sh;pip3 install --trusted-host pypi.python.org %s" % item
                self.prefab.core.run(self.replace(C), shell=True)
                self.doneSet("pip3_%s" % item)

    def install(self):
        if not self.doneGet("build"):
            self.build()
        self.prefab.core.dir_ensure(j.dirs.JSBASEDIR)
        self.prefab.core.dir_ensure(j.dirs.JSBASEDIR + "/bin")
        self.prefab.core.dir_ensure(j.dirs.JSBASEDIR + "/lib")
        command = """
        rsync -ldr --ignore-existing {python_build}/bin/* {JSBASE}/bin
        rsync -ldr --ignore-existing {python_build}/lib/* {JSBASE}/lib
        cp -r {python_build}/include {JSBASE}/include
        cp -r {python_build}/plib    {JSBASE}/plib
        cp {python_build}/env.sh {JSBASE}/env.sh
        cp {python_build}/_sysconfigdata_m_linux_x86_64-linux-gnu.py {JSBASE}
        """.format(python_build=self.BUILDDIRL, JSBASE=j.dirs.JSBASEDIR)

        self.prefab.core.run(command)
        C = """
        autoconf
        libffi-dev
        gcc
        make
        build-essential
        autoconf
        libtool
        pkg-config
        libpq-dev
        libsqlite3-dev
        """
        self.prefab.package.multiInstall(C)
