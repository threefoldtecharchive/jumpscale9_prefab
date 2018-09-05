from jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabPython(base):

    def _init(self):
        self.logger_enable()
        self.BUILDDIRL = self.core.replace("$BUILDDIR/python3/")
        self.CODEDIRL = self.core.replace("$BUILDDIR/code/python3/")
        self.JUMPSCALE_BRANCH = "development"
        self.include_jumpscale = True

    def reset(self):
        """
        is a quite serious reset, to make sure we really install everything required
        """
        j.tools.prefab.reset()
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)
        self.prefab.runtimes.pip.reset()
        self.prefab.system.package.reset()

    def build(self, jumpscale_branch='development', include_jumpscale=True, reset=False):
        """
        js_shell 'j.tools.prefab.local.runtimes.python.build(reset=True)'


        will build python and install all pip's inside the build directory

        """

        if reset:
            self.reset()

        if self.doneCheck("build", reset):
            return

        self.JUMPSCALE_BRANCH = jumpscale_branch
        self.include_jumpscale = include_jumpscale
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
                mkdir -p {builddir} 

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

        self._pip_env_install(reset=reset)

        return self.BUILDDIRL

    def _pip_env_install(self, reset=False):
        """

        will make sure we add env scripts to it as well as add all the required pip modules

        js_shell 'j.tools.prefab.local.runtimes.python._pip_env_install(reset=True)'
        """

        C = """

        source env.sh

        export PBASE=`pwd`

        export OPENSSLPATH={}

        export PATH=$PATH:$OPENSSLPATH/bin:/usr/local/bin:/usr/bin:/bin

        export LIBRARY_PATH="$LIBRARY_PATH:$OPENSSLPATH/lib:/usr/lib:/usr/local/lib:/lib:/lib/x86_64-linux-gnu"
        export LD_LIBRARY_PATH="$LIBRARY_PATH"

        export CPPPATH="$PBASE/include/python3.6m:$OPENSSLPATH/include:/usr/include"
        export CPATH="$CPPPATH"

        export CFLAGS="-I$CPATH/"
        export CPPFLAGS="-I$CPATH/"
        export LDFLAGS="-L$LIBRARY_PATH/"
        
        find $PBASE -name \*.pyc -delete
        find $PBASE/code/github/threefoldtech -name \*.pyc -delete 2>&1 > /dev/null || echo

        """.format("(brew --prefix openssl)" if self.core.isMac else "(which openssl)")
        C = self.replace(C)
        self.prefab.core.file_write("%s/envbuild.sh" % self.BUILDDIRL, C)

        C = """
        export PBASE=`pwd`

        export PATH=$PBASE/bin:/usr/local/bin:/usr/bin
        export PYTHONPATH=$PBASE/lib/pythonbin:$PBASE/lib:$PBASE/lib/python3.6:$PBASE/lib/python3.6/lib-dynload:$PBASE/bin
        export PYTHONHOME=$PBASE

        export LIBRARY_PATH="$PBASE/bin:$PBASE/lib"
        export LD_LIBRARY_PATH="$LIBRARY_PATH"

        export LDFLAGS="-L$LIBRARY_PATH/"

        export LC_ALL=en_US.UTF-8
        export LANG=en_US.UTF-8

        export PS1="JUMPSCALE: "
        
        find $PBASE -name \*.pyc -delete
        find $PBASE/code/github/threefoldtech -name \*.pyc -delete 2>&1 > /dev/null || echo

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

        if self.include_jumpscale:
            self._include_jumpscale(reset=reset)
            # self._install_portal(self.JUMPSCALE_BRANCH)

        self._pip_all(reset=reset)

        msg = "\n\nto test do:\ncd $BUILDDIRL;source env.sh;python3"
        msg = self.replace(msg)
        self.logger.info(msg)

    # def _install_portal(self, branch):
    #     self.prefab.web.portal.install(start=False, branch=branch)
    #     dest_robot_portal = self.prefab.core.dir_paths['JSAPPSDIR'] + '/0-robot-portal'
    #     self.prefab.web.zrobotportal.install(dest=dest_robot_portal, start_portal=False)

    def _pip_all(self,reset=False):
        """
        install pips which are not part of the jumpscale installs yet
        """
        C="""
        git+https://github.com/spesmilo/electrum.git@3.2.2
        """

        self._pip(C)

    def _include_jumpscale(self, reset=True):
        """
        js_shell 'j.tools.prefab.local.runtimes.python._include_jumpscale(reset=False)'
        """
        if self.doneCheck("_include_jumpscale", reset):
            return

        self.core.dir_ensure("%s/lib/pythonbin" % self.BUILDDIRL)
        self.core.file_write("%s/lib/pythonbin/__init__.py" % self.BUILDDIRL,"")  #touch for init

        todo=[]
        todo.append("https://github.com/threefoldtech/jumpscale_core")
        todo.append("https://github.com/threefoldtech/jumpscale_lib")
        todo.append("https://github.com/threefoldtech/jumpscale_prefab")
        todo.append("https://github.com/threefoldtech/digital_me")
        todo.append("https://github.com/threefoldtech/0-robot")
        todo.append("https://github.com/threefoldtech/0-templates")
        todo.append("https://github.com/threefoldtech/digital_me_recipes")

        for item in todo:
            #TODO this is super ugly. We need to implement this in prefabGit
            cmd = "js_shell 'print(j.clients.git.getContentPathFromURLorPath(\"%s\"))'"% item
            _,path,_ = self.core.run(cmd)
            if self.core.file_exists("%s/setup.py"%path):
                C = "set -e;cd $BUILDDIRL;source envbuild.sh;cd %s;pip3 install -e . --trusted-host pypi.python.org" % path
                self.prefab.core.run(self.replace(C), shell=True)

        self._pip_all()


        # C = """
        # git+https://github.com/threefoldtech/jumpscale_core@{0}#egg=core
        # git+https://github.com/threefoldtech/jumpscale_lib@{0}
        # git+https://github.com/threefoldtech/jumpscale_prefab@{0}
        # git+https://github.com/threefoldtech/0-robot@{0}
        # git+https://threefoldtech/0-hub#egg=zerohub&subdirectory=client
        # """.format(self.JUMPSCALE_BRANCH)

        # we need to pull 0-robot and recordchain repo first to fix issue with the generate function that is called during the installations
        # j.clients.git.pullGitRepo(url='https://github.com/threefoldtech/0-robot', branch=self.JUMPSCALE_BRANCH, ssh=False)
        # self._pip(C, reset=reset)
        #
        # self.prefab.zero_os.zos_stor_client.build(python_build=True)  # builds the zos_stor_client
        #
        # # self.sandbox(deps=False)
        # self.doneSet("_include_jumpscale")

    # need to do it here because all runs in the sandbox
    def _pip(self, pips, reset=False):
        for item in pips.split("\n"):
            item = item.strip()
            if item == "":
                continue
            # cannot use prefab functionality because would not be sandboxed
            if not self.doneGet("pip3_%s" % item) or reset:
                C = "set -e;cd $BUILDDIRL;source envbuild.sh;pip3 install --trusted-host pypi.python.org %s" % item
                self.prefab.core.run(self.replace(C), shell=True)
                self.doneSet("pip3_%s" % item)

