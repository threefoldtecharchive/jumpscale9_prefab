from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabPython(base):

    def _init(self):
        self.logger_enable()
        self.BUILDDIRL = self.core.replace("$BUILDDIR/python3/")
        self.CODEDIRL = self.core.replace("$BUILDDIR/code/python3/")
        self.OPENSSLPATH = self.core.replace("$BUILDDIR/openssl")
        self.JUMPSCALE_BRANCH = "development_961"

    def reset(self):
        base.reset(self)
        self.core.dir_remove(self.BUILDDIRL)
        self.core.dir_remove(self.CODEDIRL)
        self.prefab.runtimes.pip.reset()

    def build(self, jumpscale_branch='development', include_jumpscale=True, reset=False,tag="v3.6.7"):
        """
        js_shell 'j.tools.prefab.local.runtimes.python.build(reset=False)'
        js_shell 'j.tools.prefab.local.runtimes.python.build(reset=True)'


        will build python and install all pip's inside the builded directory

        possible tags: v3.7.1, v3.6.7

        """

        if reset:
            self.reset()

        if self.doneCheck("build", reset):
            return

        self.JUMPSCALE_BRANCH = jumpscale_branch
        self.include_jumpscale = include_jumpscale
        self.prefab.system.installbase.development(python=False)  # make sure all required components are there

        if not self.doneGet("compile") or reset:

            self.prefab.tools.git.pullRepo('https://github.com/python/cpython', dest=self.CODEDIRL, tag=tag,reset=True, ssh=False)

            if self.core.isMac:
                # clue to get it finally working was in https://stackoverflow.com/questions/46457404/how-can-i-compile-python-3-6-2-on-macos-with-openssl-from-homebrew

                C = """
                set -ex
                cd $CODEDIRL
                mkdir -p $BUILDDIRL

                # export OPENSSLPATH=$(brew --prefix openssl)
                
                export OPENSSLPATH=$OPENSSLPATH
                
                # export CPPFLAGS=-I/opt/X11/include
                # export CFLAGS="-I$(brew --prefix openssl)/include" LDFLAGS="-L$(brew --prefix openssl)/lib"                

                ./configure --prefix=$BUILDDIRL  CPPFLAGS="-I$OPENSSLPATH/include" LDFLAGS="-L$OPENSSLPATH/lib"

                #if you do the optimizations then it will do all the tests
                # ./configure --prefix=$BUILDDIRL --enable-optimizations
                
                # make -j12

                make -j12 EXTRATESTOPTS=--list-tests install
                """
                C = self.replace(C)

            else:

                # self.prefab.tools.git.pullRepo('https://github.com/python/cpython', dest=self.CODEDIRL, tag="3.7.1",
                #                            reset=False, ssh=False)

                self.prefab.tools.git.pullRepo('https://github.com/python/cpython', dest=self.CODEDIRL, tag="v3.6.7",reset=True, ssh=False)


                # on ubuntu 1604 it was all working with default libs, no reason to do it ourselves
                self.prefab.system.package.install('zlib1g-dev,libncurses5-dev,libbz2-dev,liblzma-dev,libsqlite3-dev,libreadline-dev,libssl-dev,libsnappy-dev')

                C = """

                apt install wget gcc make -y

                set -ex
                cd $CODEDIRL
                
                export OPENSSLPATH=$OPENSSLPATH

                ./configure --prefix=$BUILDDIRL --enable-optimizations  #THIS WILL MAKE SURE ALL TESTS ARE DONE, WILL TAKE LONG TIME

                make clean
                # make -j4
                make -j8 EXTRATESTOPTS=--list-tests install
                # make install
                """
                C = self.replace(C)

            self.prefab.core.file_write("%s/mycompile_all.sh" % self.CODEDIRL, C)

            self.logger.info("compile python3")
            self.logger.debug(C)
            self.prefab.core.run("bash %s/mycompile_all.sh" % self.CODEDIRL, sudo=True)  # makes it easy to test & make changes where required

            #test openssl is working
            cmd = "~/opt/var/build/python3/bin/python3 -c 'import ssl'"
            rc,out,err=self.prefab.core.run(cmd,die=False)
            if rc>0:
                raise RuntimeError("SSL was not included well\n%s"%err)

            self.doneSet("compile")


        self._addPIP(reset=reset,tag=tag)

        return self.BUILDDIRL

    def _addPIP(self, reset=False,tag="v3.6.7"):
        """

        will make sure we add env scripts to it as well as add all the required pip modules

        js_shell 'j.tools.prefab.local.runtimes.python._addPIP(reset=True)'
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
        export PYTHONHTTPSVERIFY=0
        
        export PATH=$PBASE/bin:/usr/local/bin:/usr/bin
        export PYTHONPATH=$PBASE/lib/python.zip:$PBASE/lib:$PBASE/lib/python3.6:$PBASE/lib/python3.6/site-packages:$PBASE/lib/python3.6/lib-dynload:$PBASE/bin
        export PYTHONHOME=$PBASE

        export LIBRARY_PATH="$PBASE/bin:$PBASE/lib"
        export LD_LIBRARY_PATH="$LIBRARY_PATH"

        export LDFLAGS="-L$LIBRARY_PATH/"

        export LC_ALL=en_US.UTF-8
        export LANG=en_US.UTF-8

        export PS1="JUMPSCALE: "

        """
        self.prefab.core.file_write("%s/env.sh" % self.BUILDDIRL, C)

        if not self.doneGet("pip3install") or reset:
            C = """
            cd $BUILDDIRL
            . envbuild.sh
            set -e                        
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

        self._pipAll(reset=reset)

        msg = "\n\nto test do:\ncd $BUILDDIRL;source env.sh;python3"
        msg = self.replace(msg)
        self.logger.info(msg)

    def _install_portal(self, branch):
        self.prefab.web.portal.install(start=False, branch=branch)
        dest_robot_portal = self.prefab.core.dir_paths['JSAPPSDIR'] + '/0-robot-portal'
        self.prefab.web.zrobotportal.install(dest=dest_robot_portal, start_portal=False)

    def _pipAll(self, reset=False):
        """
        js_shell 'j.tools.prefab.local.runtimes.python._pipAll(reset=False)'
        """
        # needs at least items from /JS8/code/github/threefoldtech/jumpscale_core/install/dependencies.py
        if self.doneCheck("pipall", reset):
            return

        #need to build right version of capnp
        self.prefab.lib.capnp.build()

        C="""
        #CORE
        'certifi',
        'Cython',
        'GitPython>=2.1.1',
        'click>=6.6',
        'colored_traceback',
        'colorlog>=2.10.0',
        'httplib2>=0.9.2',
        'ipython<6.5.0,>=6.0.0',
        'jinja2',
        'libtmux>=0.7.1',
        'netaddr>=0.7.18',
        'path.py>=10.3.1',
        'pystache>=0.5.4',
        'python-dateutil>=2.5.3',
        'pytoml>=0.1.2',
        'toml',
        'redis>=2.10.5',
        'requests>=2.12.0',
        'future>=0.15.0',
        'watchdog',
        'msgpack-python',
        'npyscreen',
        'pyyaml',
        'pyserial>=3.0'
        'docker>=3',
        'fakeredis',
        'ssh2-python',
        'parallel_ssh>=1.4.0',
        'psutil>=5.0.1',
        'Unidecode>=0.04.19',  
        #LIB
        'Brotli>=0.6.0',
        'Jinja2>=2.9.6',
        'Pillow>=4.1.1',
        'PyGithub>=1.34',
        # 'SQLAlchemy>=1.1.9',
        'colored-traceback>=0.2.2',
        'colorlog>=2.10.0',
        'cson>=0.7',
        'docker>=2.2.1',
        'gevent>=1.2.1',
        'grequests>=0.3.0',
        'influxdb>=4.1.0',
        'msgpack-python>=0.4.8',
        'netaddr>=0.7.19',
        'netifaces>=0.10.5',
        'ovh>=0.4.7',
        'paramiko>=2.2.3',
        'path.py>=10.3.1',
        'peewee>=2.9.2',
        'psycopg2>=2.7.1',
        'pudb>=2017.1.2',
        'cryptography>=2.2.0',
        'pyOpenSSL>=17.0.0',
        'pyblake2>=0.9.3',
        'pymux>=0.13',
        # 'pypandoc>=1.3.3',
        'redis>=2.10.5',
        'requests>=2.13.0',
        'toml>=0.9.2',
        # 'uvloop>=0.8.0',
        'watchdog>=0.8.3',
        'dnspython>=1.15.0',
        'etcd3>=0.7.0',
        'zerotier>=1.1.2',
        'packet-python>=1.37',
        'blosc>=1.5.1',
        'pynacl>=1.2.1',
        'ipcalc>=1.99.0',
        'ed25519>=1.4',
        'python-jose>=1.3.2',
        'html2text'      
        #DIGITALME
        'Jinja2>=2.9.6',
        'gevent>=1.2.1',
        'gevent-websocket',
        'grequests>=0.3.0',
        'peewee>=2.9.2',
        'pudb>=2017.1.2',
        'redis>=2.10.5',
        'requests>=2.13.0',
        'toml>=0.9.2',
        'watchdog>=0.8.3',
        'dnspython>=1.15.0',
        'zerotier>=1.1.2',
        'blosc>=1.5.1',
        'pynacl>=1.1.2',
        'ipcalc>=1.99.0',
        'ed25519>=1.4',
        'python-jose>=1.3.2',
        'gipc',
        'cryptocompare',
        'dnslib',
        'pycountry',
        'graphene>=2.0',                
        #PREFAB
        'asyncssh>=1.9.0',
        'pymongo>=3.4.0',  
         #ZROBOT
        'Flask>=0.12.2',
        'Flask-Inputs>=0.2.0',         
        'itsdangerous>=0.24',
        'jsonschema>=2.5.1',
        'six>=1.10.0',
        'python-jose>=2.0.1',
        'gevent >= 1.2.2',
        'psutil>=5.4.3',
        'prometheus_client>=0.1.1',
        'netifaces>=0.10.6',
        'msgpack-python>=0.4.8',   
        'pycapnp>=0.5.12',                   
        """

        self._pip(C)

        if not self.core.isMac:
            self.prefab.zero_os.zos_stor_client.build(python_build=True)  # builds the zos_stor_client
            self._pip("g8storclient")

        # self.sandbox(deps=False)
        self.doneSet("pipall")

    def _jumpscale(self):
        C = """
        git+https://github.com/threefoldtech/jumpscale_core@{0}#egg=core
        git+https://github.com/threefoldtech/jumpscale_lib@{0}
        git+https://github.com/threefoldtech/jumpscale_prefab@{0}
        git+https://github.com/threefoldtech/0-robot@{0}
        git+https://threefoldtech/0-hub#egg=zerohub&subdirectory=client
        """.format(self.JUMPSCALE_BRANCH)
        # we need to pull 0-robot repo first to fix issue with the generate function that is called during the installations ???
        j.clients.git.pullGitRepo(url='https://github.com/threefoldtech/0-robot', branch=self.JUMPSCALE_BRANCH, ssh=False)
        self._pip(C)


    # need to do it here because all runs in the sandbox
    def _pip(self, pips, reset=False):
        for item in pips.split("\n"):
            item = item.strip().strip(",").strip("'").strip("\"").strip()
            if item == "":
                continue
            if item.startswith("#"):
                continue
            item = "'%s'"%item
            # cannot use prefab functionality because would not be sandboxed
            if not self.doneGet("pip3_%s" % item) or reset:
                C = "set -ex;cd $BUILDDIRL;source envbuild.sh;pip3 install --trusted-host pypi.python.org %s" % item
                self.prefab.core.run(self.replace(C), shell=True)
                self.doneSet("pip3_%s" % item)


