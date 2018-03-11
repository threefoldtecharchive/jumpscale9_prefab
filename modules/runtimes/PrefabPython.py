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
        self.prefab.runtimes.pip.reset()

    def build(self, reset=False):
        """
        js9 'j.tools.prefab.local.runtimes.python.build()'


        will build python and install all pip's inside the builded directory

        """

        if reset:
            self.reset()

        if self.doneCheck("build", reset):
            return

        self.prefab.system.base.development(python=False) #make sure all required components are there

        if not self.doneGet("compile") or reset:
            cpath = self.prefab.tools.git.pullRepo('https://github.com/python/cpython', branch="3.6", reset=False)
            #TODO:*1 there seems to be something wrong here, keeps on redoing the pull, should only do this once
            assert cpath.rstrip("/") == self.CODEDIRL.rstrip("/")

            ##TODO:*1 GET THIS TO WORK ON LINUX & OSX (couldn't get the ssl to work)
            if self.core.isMac:  
                self.prefab.lib.openssl.build()
                # self.prefab.lib.libffi.build()

                if not self.doneGet("xcode_install"):
                    self.prefab.core.run(
                        "xcode-select --install", die=False, showout=True)
                    C = """
                    openssl
                    xz
                    """
                    self.prefab.system.package.install(C)
                    self.doneSet("xcode_install")

                C = """
                set -ex
                cd $CODEDIRL
                mkdir -p $BUILDDIRL

                # export LIBRARY_PATH="$openssldir/lib:$libffidir/lib:/usr/lib/x86_64-linux-gnu:/usr/lib:/usr/local/lib"
                # export LD_LIBRARY_PATH="$openssldir/lib:$libffidir/lib:/usr/lib/x86_64-linux-gnu:/usr/lib:/usr/local/lib"
                export LIBRARY_PATH="$openssldir/lib:$libffidir/lib:/usr/lib:/usr/local/lib"
                export LD_LIBRARY_PATH="$openssldir/lib:$libffidir/lib:/usr/lib:/usr/local/lib"
                export CPPPATH="$openssldir/include:/usr/include"
                export CPATH="$openssldir/include:/usr/include"
                export PATH=$openssldir/lib:/$openssldir/bin:/usr/local/bin:/usr/bin:/bin

                export CFLAGS="-I$CPATH/"
                export CPPFLAGS="-I$CPATH/"
                export LDFLAGS="-L$LIBRARY_PATH/"
                # export LDFLAGS="-L$openssldirlib"

                echo $CFLAGS
                echo $LDFLAGS

                ./configure --prefix=$BUILDDIRL

                #if you do the optimizations then it will do all the tests
                # ./configure --prefix=$BUILDDIRL --enable-optimizations
                
                # make -s -j8
                # mkdir -p dbuild
                # make -C dbuild 
                make -j8 EXTRATESTOPTS=--list-tests install


                """

                C = C.replace("$openssldir", self.prefab.lib.openssl.BUILDDIRL.rstrip("/"))
                C = C.replace("$libffidir", self.prefab.lib.libffi.BUILDDIRL.rstrip("/"))
                C = self.replace(C)

            else: 

                #on ubuntu 1604 it was all working with default libs, no reason to do it ourselves
                self.prefab.system.package.install('zlib1g-dev,libncurses5-dev,libbz2-dev,liblzma-dev,libsqlite3-dev,libreadline-dev,libssl-dev')

                C = """

                apt install wget gcc make -y

                set -ex
                cd {codedir}

                ./configure --prefix={builddir} --enable-optimizations  #THIS WILL MAKE SURE ALL TESTS ARE DONE, WILL TAKE LONG TIME

                make clean
                # make -j4
                make -j8 EXTRATESTOPTS=--list-tests install
                # make install
                """.format(builddir=self.BUILDDIRL, codedir=self.CODEDIRL, openssldir=self.prefab.lib.openssl.BUILDDIRL)

            self.prefab.core.file_write("%s/mycompile_all.sh" % self.CODEDIRL, C)

            self.logger.info("compile python3")
            self.logger.debug(C)
            self.prefab.core.run("cd %s;bash mycompile_all.sh" % self.CODEDIRL) #makes it easy to test & make changes where required

            self.doneSet("compile")

        self._package(reset=reset)

        return self.BUILDDIRL

    def _package(self, reset=False):
        """

        will make sure we add env scripts to it as well as add all the required pip modules

        js9 'j.tools.prefab.local.runtimes.python._package(reset=True)'
        """

        C="""

        source env.sh

        export PBASE=`pwd`

        export PATH=$PATH:$openssldir/bin:/usr/local/bin:/usr/bin:/bin

        export LIBRARY_PATH="$LIBRARY_PATH:$openssldir/lib:$libffidir/lib:/usr/lib:/usr/local/lib:/lib:/lib/x86_64-linux-gnu"
        export LD_LIBRARY_PATH="$LIBRARY_PATH"

        export CPPPATH="$PBASE/include/python3.6m:$openssldir/include:/usr/include"
        export CPATH="$CPPPATH"

        export CFLAGS="-I$CPATH/"
        export CPPFLAGS="-I$CPATH/"
        export LDFLAGS="-L$LIBRARY_PATH/"


        #python -s -S $@
        """
        C = C.replace("$openssldir", self.prefab.lib.openssl.BUILDDIRL.rstrip("/"))
        C = C.replace("$libffidir", self.prefab.lib.libffi.BUILDDIRL.rstrip("/"))
        C = self.replace(C)        
        self.prefab.core.file_write("%s/envbuild.sh" %  self.BUILDDIRL, C)   

        C="""
        export PBASE=`pwd`

        export PATH=$PBASE/bin:/usr/local/bin:/usr/bin
        export PYTHONPATH=$PBASE/lib/python.zip:$PBASE/lib:$PBASE/lib/python3.6:$PBASE/lib/python3.6/lib-dynload:$PBASE/bin
        export PYTHONHOME=$PBASE

        export LIBRARY_PATH="$PBASE/bin:$PBASE/lib"
        export LD_LIBRARY_PATH="$LIBRARY_PATH"

        export LDFLAGS="-L$LIBRARY_PATH/"

        export LC_ALL=en_US.UTF-8
        export LANG=en_US.UTF-8

        export PS1="JS9: "        

        """
        self.prefab.core.file_write("%s/env.sh" %  self.BUILDDIRL, C)           

        if not self.doneGet("pip3install") or reset:
            C = """
            set -ex
            cd $BUILDDIRL
            . envbuild.sh
            rm -rf get-pip.py
            curl https://bootstrap.pypa.io/get-pip.py > get-pip.py
            $BUILDDIRL/bin/python3 get-pip.py
            """
            C = self.replace(C)        
            self.prefab.core.file_write("%s/pip3build.sh" % self.BUILDDIRL, C)   
            self.prefab.core.run("cd %s;bash pip3build.sh" % self.BUILDDIRL)
        self.doneSet("pip3install")

        if not self.core.isMac:
            self.prefab.system.package.ensure("libssl-dev") 
            #for osx SHOULD NOT BE DONE BECAUSE WE SHOULD HAVE IT BUILD BEFORE AND ARE USING I FOR OSX
            self.prefab.system.package.ensure("libcapnp-dev")
        else:
            self.prefab.system.package.ensure("capnp")  #hope this installs the dev libs as well on osx

        self._pipAll(reset=reset)

        msg = "\n\nto test do:\ncd $BUILDDIRL;source env.sh;python3"
        msg = self.replace(msg)
        self.logger.info(msg)


    def _pipAll(self, reset=False):
        # needs at least items from /JS8/code/github/jumpscale/jumpscale_core9/install/dependencies.py
        if self.doneCheck("pipall", reset):
            return
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
        pudb
        requests
        netaddr
        ipython
        cython
        pycapnp
        path.py
        colored-traceback
        colorlog
        msgpack-python
        pyblake2
        brotli
        pysodium
        curio
        uvloop
        gevent
        pystache
        httplib2
        python-jose
        python-dateutil
        docker
        jsonschema
        sanic
        pytoml
        autopep8
        asyncssh

        """
        self._pip(C, reset=reset)
        # self.sandbox(deps=False)
        self.doneSet("pipall")

    #need to do it here because all runs in the sandbox
    def _pip(self, pips, reset=False):
        for item in pips.split("\n"):
            item = item.strip()
            if item == "":
                continue
            # cannot use prefab functionality because would not be sandboxed
            if not self.doneGet("pip3_%s" % item) or reset:
                C = "set -ex;cd $BUILDDIRL;source envbuild.sh;pip3 install --trusted-host pypi.python.org %s" % item
                self.prefab.core.run(self.replace(C), shell=True)
                self.doneSet("pip3_%s" % item)



    #BELOW IS FOR LATER, LETS MAKE SURE WE HAVE THE BUILDING & PIP GOING WELL


    # def install(self):
    #     """
    #     will not use the platform python, will be build from scratch
    #     """
    #     if self.doneCheck("install", reset):
    #         return
    #     self.build()
    #     self.prefab.core.dir_ensure(j.dirs.JSBASEDIR)
    #     self.prefab.core.dir_ensure(j.dirs.JSBASEDIR + "/bin")
    #     self.prefab.core.dir_ensure(j.dirs.JSBASEDIR + "/lib")
    #     command = """
    #     rsync -ldr --ignore-existing {python_build}/bin/* {JSBASE}/bin
    #     rsync -ldr --ignore-existing {python_build}/lib/* {JSBASE}/lib
    #     cp -r {python_build}/include {JSBASE}/include
    #     cp -r {python_build}/plib    {JSBASE}/plib
    #     cp {python_build}/env.sh {JSBASE}/env.sh
    #     cp {python_build}/_sysconfigdata_m_linux_x86_64-linux-gnu.py {JSBASE}
    #     """.format(python_build=self.BUILDDIRL, JSBASE=j.dirs.JSBASEDIR)

    #     self.prefab.core.run(command)







    # def sandbox(self, reset=False, deps=True):
    #     if deps:
    #         self.build(reset=reset)
    #     if self.doneCheck("sandbox", reset):
    #         return

    #     C = """
    #     set -ex
    #     cd $BUILDDIRL

    #     rm -rf share
    #     mkdir -p lib/python3.6/site-packages/
    #     rsync -rav lib/python3.6/site-packages/ plib/site-packages/
    #     rm -rf lib/python3.6
    #     find . -name '*.pyc' -delete

    #     find . -name 'get-pip.py' -delete
    #     set +ex
    #     find -L .  -name '__pycache__' -exec rm -rf {} \;
    #     find . -name "*.dist-info" -exec rm -rf {} \;
    #     find . -name "*.so" -exec mv {} lib/ \;

    #     # rm -f _sysconfigdata_m_darwin_darwin.py
    #     rm -f openssl*

    #     """
    #     self.prefab.core.run(self.replace(C))

    #     # now copy jumpscale in
    #     linkpath = "%s/lib/JumpScale" % self.prefab.core.dir_paths["JSBASEDIR"]
    #     C = "ln -s %s %s/lib/JumpScale" % (linkpath, self.BUILDDIRL)
    #     if not self.prefab.core.file_exists("%s/lib/JumpScale" % self.BUILDDIRL):
    #         self.core.run('rm -rf %s/lib/JumpScale' % self.BUILDDIRL)
    #         self.prefab.core.run(C)

    #     # # now create packaged dir
    #     # destpath2 = self.BUILDDIRL.rstrip("/").rstrip() + "2"
    #     # self.prefab.core.copyTree(source=self.BUILDDIRL, dest=destpath2, keepsymlinks=False, deletefirst=True,
    #     #                            overwriteFiles=True,
    #     #                            recursive=True, rsyncdelete=True, createdir=True)

    #     # zip trick does not work yet lets leave for now
    #     # C = """
    #     # set -ex
    #     # cd %s/plib
    #     # zip -r ../plib.zip *
    #     # cd ..
    #     # rm -rf plib
    #     # """ % destpath2
    #     # self.prefab.core.run(C)