from js9 import j

base = j.tools.prefab._getBaseClass()


class PrefabPython(base):

    def _init(self):
        self.logger_enable()
        self.BUILDDIRL = self.core.replace("$BUILDDIR/python3/")
        self.CODEDIRL = self.core.replace("$BUILDDIR/code/python3/")
        self.JS9_BRANCH = None
        self.include_js9 = None

    def reset(self):
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)
        self.prefab.runtimes.pip.reset()

    def build(self, js9_branch='development', include_js9=True, reset=False):
        """
        js9 'j.tools.prefab.local.runtimes.python.build(reset=False)'


        will build python and install all pip's inside the builded directory

        """

        if reset:
            self.reset()

        if self.doneCheck("build", reset):
            return
        
        self.JS9_BRANCH = js9_branch
        self.include_js9 = include_js9
        self.prefab.system.base.development(python=False)  # make sure all required components are there

        if not self.doneGet("compile") or reset:
            self.prefab.tools.git.pullRepo('https://github.com/python/cpython', dest=self.CODEDIRL, branch="3.6", reset=False, ssh=False)

            if self.core.isMac:
                # clue to get it finally working was in https://stackoverflow.com/questions/46457404/how-can-i-compile-python-3-6-2-on-macos-with-openssl-from-homebrew
                if reset or not self.doneGet("xcode_install"):
                    self.prefab.core.run(
                        "xcode-select --install", die=False, showout=True)
                    C = """
                    openssl
                    xz
                    libffi
                    """
                    self.prefab.system.package.install(C)
                    self.doneSet("xcode_install")

                C = """
                set -ex
                cd $CODEDIRL
                mkdir -p $BUILDDIRL

                export OPENSSLPATH=$(brew --prefix openssl)

                ./configure --prefix=$BUILDDIRL  CPPFLAGS="-I$OPENSSLPATH/include" LDFLAGS="-L$OPENSSLPATH/lib" 

                #if you do the optimizations then it will do all the tests
                # ./configure --prefix=$BUILDDIRL --enable-optimizations
                
                make -j8 EXTRATESTOPTS=--list-tests install
                """
                C = self.replace(C)

            else:

                # on ubuntu 1604 it was all working with default libs, no reason to do it ourselves
                self.prefab.system.package.install('zlib1g-dev,libncurses5-dev,libbz2-dev,liblzma-dev,libsqlite3-dev,libreadline-dev,libssl-dev,libsnappy-dev')

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
            self.prefab.core.run("bash %s/mycompile_all.sh" % self.CODEDIRL, sudo=True)  # makes it easy to test & make changes where required

            self.doneSet("compile")

        self._package(reset=reset)

        return self.BUILDDIRL

    def _package(self, reset=False):
        """

        will make sure we add env scripts to it as well as add all the required pip modules

        js9 'j.tools.prefab.local.runtimes.python._package(reset=True)'
        """

        C = """

        source env.sh

        export PBASE=`pwd`

        export OPENSSLPATH=$(brew --prefix openssl)

        export PATH=$PATH:$OPENSSLPATH/bin:/usr/local/bin:/usr/bin:/bin

        export LIBRARY_PATH="$LIBRARY_PATH:$OPENSSLPATH/lib:/usr/lib:/usr/local/lib:/lib:/lib/x86_64-linux-gnu"
        export LD_LIBRARY_PATH="$LIBRARY_PATH"

        export CPPPATH="$PBASE/include/python3.6m:$OPENSSLPATH/include:/usr/include"
        export CPATH="$CPPPATH"

        export CFLAGS="-I$CPATH/"
        export CPPFLAGS="-I$CPATH/"
        export LDFLAGS="-L$LIBRARY_PATH/"

        """
        C = self.replace(C)
        self.prefab.core.file_write("%s/envbuild.sh" % self.BUILDDIRL, C)

        C = """
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
        self.prefab.core.file_write("%s/env.sh" % self.BUILDDIRL, C)

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
            # for osx SHOULD NOT BE DONE BECAUSE WE SHOULD HAVE IT BUILD BEFORE AND ARE USING I FOR OSX
            self.prefab.system.package.ensure("libcapnp-dev")
        else:
            self.prefab.system.package.ensure("capnp")

        if self.include_js9:
            self._pipAll(reset=reset)

        msg = "\n\nto test do:\ncd $BUILDDIRL;source env.sh;python3"
        msg = self.replace(msg)
        self.logger.info(msg)

    def _pipAll(self, reset=False):
        """
        js9 'j.tools.prefab.local.runtimes.python._pipAll(reset=False)'
        """
        # needs at least items from /JS8/code/github/jumpscale/jumpscale_core9/install/dependencies.py
        if self.doneCheck("pipall", reset):
            return
        C = """
        git+https://github.com/Jumpscale/core9@{0}
        git+https://github.com/Jumpscale/lib9@{0}
        git+https://github.com/Jumpscale/prefab9@{0}
        """.format(self.JS9_BRANCH)
        self._pip(C, reset=reset)
        
        j.clients.git.pullGitRepo(url='https://github.com/rivine/recordchain.git')
        C = """git+https://github.com/rivine/recordchain@master"""
        self._pip(C, reset=reset)
        
        j.clients.git.pullGitRepo(url='https://github.com/zero-os/0-robot.git')
        C = """git+https://github.com/zero-os/0-robot@master"""
        self._pip(C, reset=reset)        
      
        # self.sandbox(deps=False)
        self.doneSet("pipall")

    # need to do it here because all runs in the sandbox
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

        self.prefab.zero_os.zos_stor_client.build(python_build=True)  # builds the zos_stor_client
