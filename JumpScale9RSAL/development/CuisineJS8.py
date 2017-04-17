from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineJS8(base):

    def install(self, reset=False, deps=True, branch='8.2.0', keep=False):

        if not reset and self.doneGet("install"):
            return

        if reset:
            self.cuisine.package.ensure('psmisc')
            for process in ['mongodb', 'redis', 'redis-server', 'ardb-server', 'tmux']:
                self.cuisine.core.run('killall %s' % process, die=False)
            C = """
            rm -f $TMPDIR/jsexecutor*
            rm -f $TMPDIR/jsinstall*
            rm -rf $TMPDIR/actions*
            set -ex
            rm -rf /opt/*
            """
            self.cuisine.core.run(C, die=False)

        if branch != "master":
            C = """
            set -ex
            apt install curl -y
            cd $TMPDIR
            rm -f install.sh
            export JSBRANCH="$branch"
            curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core9/$JSBRANCH/install/install.sh?$RANDOM > install.sh
            bash install.sh
            """
            C = C.replace("$branch", branch)
            self.cuisine.core.run(C)
        else:
            C = """
            set -ex
            apt install curl -y
            cd $TMPDIR
            rm -f install.sh
            curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core9/master/install/install.sh?$RANDOM > install.sh
            bash install.sh
            """
            self.cuisine.core.run(C)

        self.doneSet("install")

    # should not do this, is otherwise different than the std install
    # def installDeps(self):
    #
    #     self.cuisine.systemservices.base.install()
    #     self.cuisine.development.python.install()
    #     self.cuisine.development.pip.ensure()
    #     self.cuisine.apps.redis.install()
    #     self.cuisine.apps.brotli.build()
    #     self.cuisine.apps.brotli.install()
    #
    #     self.cuisine.development.pip.install('pytoml')
    #     self.cuisine.development.pip.install('pygo')
    #     self.cuisine.package.ensure('libxml2-dev')
    #     self.cuisine.package.ensure('libxslt1-dev')
    #
    #     # python etcd
    #     C = """
    #     cd $TMPDIR/
    #     git clone https://github.com/jplana/python-etcd.git
    #     cd python-etcd
    #     python3 setup.py install
    #     """
    #     C = self.replace(C)
    #     self.cuisine.core.run(C)
    #
    #     # gevent
    #     C = """
    #     pip3 install 'cython>=0.23.4' git+git://github.com/gevent/gevent.git#egg=gevent
    #     """
    #     self.cuisine.core.run(C)
    #
    #     C = """
    #     # cffi==1.5.2
    #     cffi
    #     paramiko
    #
    #     msgpack-python
    #     redis
    #     #credis
    #     aioredis
    #
    #     mongoengine==0.10.6
    #
    #     certifi
    #     docker-py
    #     http://carey.geek.nz/code/python-fcrypt/fcrypt-1.3.1.tar.gz
    #
    #     gitlab3
    #     gitpython
    #     html2text
    #
    #     # pysqlite
    #     click
    #     influxdb
    #     ipdb
    #     ipython --upgrade
    #     jinja2
    #     netaddr
    #     wtforms_json
    #
    #     reparted
    #     pytoml
    #     pystache
    #     pymongo
    #     psycopg2
    #     pathtools
    #     psutil
    #
    #     pytz
    #     requests
    #     sqlalchemy
    #     urllib3
    #     zmq
    #     pyyaml
    #     python-etcd
    #     websocket
    #     marisa-trie
    #     pylzma
    #     ujson
    #     watchdog
    #     pygo
    #     pygithub
    #     minio
    #
    #     # colorlog
    #     colored-traceback
    #     #pygments
    #     tmuxp
    #
    #     ply
    #     xonsh
    #     pudb
    #
    #     traitlets
    #     python-telegram-bot
    #     colorlog
    #     path.py
    #     dnspython3
    #     packet-python
    #     gspread
    #     oauth2client
    #     crontab
    #     beautifulsoup4
    #     lxml
    #     pycapnp
    #     """
    #     self.cuisine.development.pip.multiInstall(C, upgrade=True)
    #
    #     # snappy install
    #     self.cuisine.package.ensure('libsnappy-dev')
    #     self.cuisine.package.ensure('libsnappy1v5')
    #     self.cuisine.development.pip.install('python-snappy')
    #
    #     if self.cuisine.platformtype.osname != "debian":
    #         C = """
    #         blosc
    #         bcrypt
    #         """
    #         self.cuisine.development.pip.multiInstall(C, upgrade=True)
