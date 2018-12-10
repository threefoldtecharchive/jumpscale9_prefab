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

    def build(self, reset=False,tag="v3.6.7"):
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

        self.prefab.system.installbase.development(python=False)  # make sure all required components are there



        self.prefab.tools.git.pullRepo('https://github.com/python/cpython', dest=self.CODEDIRL, tag=tag, reset=reset, ssh=False, timeout=20000)
        if not self.doneGet("compile") or reset:
            if self.core.isMac:
                # clue to get it finally working was in https://stackoverflow.com/questions/46457404/how-can-i-compile-python-3-6-2-on-macos-with-openssl-from-homebrew

                C = """
                set -ex
                cd $CODEDIRL
                mkdir -p $BUILDDIRL

                # export OPENSSLPATH=$(brew --prefix openssl)
                
                # export OPENSSLPATH=$OPENSSLPATH
                
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
                # on ubuntu 1604 it was all working with default libs, no reason to do it ourselves
                self.prefab.system.package.install('zlib1g-dev,libncurses5-dev,libbz2-dev,liblzma-dev,libsqlite3-dev,libreadline-dev,libssl-dev,libsnappy-dev')

                C = """

                apt install wget gcc make -y

                set -ex
                cd $CODEDIRL
                
                # export OPENSSLPATH=$OPENSSLPATH

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
            cmd = "source /sandbox/env.sh;/sandbox/var/build/python3/bin/python3 -c 'import ssl'"
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

    def pips_list(self,level=0):
        """
        level0 is only the most basic
        1 in the middle
        2 is all pips
        """
        C="""
        asyncssh>=1.9.0
        pystache
        blosc>=1.5.1
        Brotli>=0.6.0
        certifi
        click>=6.6
        colored-traceback>=0.2.2
        colorlog>=2.10.0
        cryptocompare
        cryptography>=2.2.0
        cson>=0.7 *
        Cython **
        dnslib
        dnspython>=1.15.0 **
        docker>=3 **
        ed25519>=1.4
        etcd3>=0.7.0 **
        fakeredis
        Flask-Inputs>=0.2.0 **
        Flask>=0.12.2 **
        future>=0.15.0
        gevent >= 1.2.2
        gevent-websocket *
        gipc
        GitPython>=2.1.1
        graphene>=2.0 *
        grequests>=0.3.0
        html2text **
        httplib2>=0.9.2
        influxdb>=4.1.0 **
        ipcalc>=1.99.0
        ipython<6.5.0>=6.0.0
        itsdangerous>=0.24 *
        Jinja2>=2.9.6
        jsonschema>=2.5.1 *
        libtmux>=0.7.1
        msgpack-python>=0.4.8
        netaddr>=0.7.19
        netifaces>=0.10.6
        netstr
        npyscreen
        ovh>=0.4.7 *
        packet-python>=1.37 *
        parallel_ssh>=1.4.0
        paramiko>=2.2.3
        path.py>=10.3.1
        peewee>=2.9.2
        Pillow>=4.1.1 *
        psutil>=5.4.3
        psycopg2>=2.7.1 *
        pudb>=2017.1.2
        pyblake2>=0.9.3
        pycapnp>=0.5.12  
        pycountry *
        PyGithub>=1.34
        pymongo>=3.4.0 **
        pymux>=0.13
        pynacl>=1.2.1
        pyOpenSSL>=17.0.0
        pypandoc>=1.3.3 **
        pyserial>=3.0
        pystache>=0.5.4 **
        python-dateutil>=2.5.3
        python-jose>=2.0.1 *
        pytoml>=0.1.2
        pyyaml
        redis>=2.10.5
        requests>=2.13.0
        six>=1.10.0
        #SQLAlchemy>=1.1.9 **
        ssh2-python *
        toml>=0.9.2
        Unidecode>=0.04.19
        uvloop>=0.8.0 *
        watchdog>=0.8.3
        zerotier>=1.1.2 *
                
        """
        res=[]
        for line in j.core.text.strip(C).split("\n"):
            if level==0 and line.find("*")!=-1:
                continue
            elif level==1 and line.find("**")!=-1:
                continue
            pip=line.strip()
            if pip.startswith("#"):
                continue
            pip=pip.replace("*","").replace("*","").strip()
            if pip=="":
                continue
            res.append(pip)
        return res

    def _pipAll(self, reset=False):
        """
        js_shell 'j.tools.prefab.local.runtimes.python._pipAll(reset=False)'
        """

        if self.doneCheck("pipall", reset):
            return

        #need to build right version of capnp
        self.prefab.lib.capnp.build()

        #list comes from /sandbox/code/github/threefoldtech/jumpscale_core/install/InstallTools.py


        self._pip(self.pips_list(3))

        if not self.core.isMac:
            self.prefab.zero_os.zos_stor_client.build(python_build=True)  # builds the zos_stor_client
            self._pip("g8storclient")

        # self.sandbox(deps=False)
        self.doneSet("pipall")


    # need to do it here because all runs in the sandbox
    def _pip(self, pips, reset=False):
        for item in pips:
            item = "'%s'"%item
            # cannot use prefab functionality because would not be sandboxed
            if not self.doneGet("pip3_%s" % item) or reset:
                C = "set -ex;cd $BUILDDIRL;source envbuild.sh;pip3 install --trusted-host pypi.python.org %s" % item
                self.prefab.core.run(self.replace(C), shell=True)
                self.doneSet("pip3_%s" % item)


