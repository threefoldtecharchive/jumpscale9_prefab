from js9 import j

base = j.tools.prefab._getBaseClass()


class CuisineJS8(base):

    def install(self, reset=False, deps=True, branch='8.2.0', keep=False):

        if not reset and self.doneGet("install"):
            return

        if reset:
            self.prefab.package.ensure('psmisc')
            for process in ['mongodb', 'redis', 'redis-server', 'ardb-server', 'tmux']:
                self.prefab.core.run('killall %s' % process, die=False)
            C = """
            rm -f $TMPDIR/jsexecutor*
            rm -f $TMPDIR/jsinstall*
            rm -rf $TMPDIR/actions*
            set -ex
            rm -rf /opt/*
            """
            self.prefab.core.run(C, die=False)

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
            self.prefab.core.run(C)
        else:
            C = """
            set -ex
            apt install curl -y
            cd $TMPDIR
            rm -f install.sh
            curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core9/master/install/install.sh?$RANDOM > install.sh
            bash install.sh
            """
            self.prefab.core.run(C)

        self.doneSet("install")

    # should not do this, is otherwise different than the std install
    # def installDeps(self):
    #
    #     self.prefab.systemservices.base.install()
    #     self.prefab.development.python.install()
    #     self.prefab.development.pip.ensure()
    #     self.prefab.apps.redis.install()
    #     self.prefab.apps.brotli.build()
    #     self.prefab.apps.brotli.install()
    #
    #     self.prefab.development.pip.install('pytoml')
    #     self.prefab.development.pip.install('pygo')
    #     self.prefab.package.ensure('libxml2-dev')
    #     self.prefab.package.ensure('libxslt1-dev')
    #
    #     # python etcd
    #     C = """
    #     cd $TMPDIR/
    #     git clone https://github.com/jplana/python-etcd.git
    #     cd python-etcd
    #     python3 setup.py install
    #     """
    #     C = self.replace(C)
    #     self.prefab.core.run(C)
    #
    #     # gevent
    #     C = """
    #     pip3 install 'cython>=0.23.4' git+git://github.com/gevent/gevent.git#egg=gevent
    #     """
    #     self.prefab.core.run(C)
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
    #     self.prefab.development.pip.multiInstall(C, upgrade=True)
    #
    #     # snappy install
    #     self.prefab.package.ensure('libsnappy-dev')
    #     self.prefab.package.ensure('libsnappy1v5')
    #     self.prefab.development.pip.install('python-snappy')
    #
    #     if self.prefab.platformtype.osname != "debian":
    #         C = """
    #         blosc
    #         bcrypt
    #         """
    #         self.prefab.development.pip.multiInstall(C, upgrade=True)
