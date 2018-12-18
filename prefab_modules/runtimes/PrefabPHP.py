from Jumpscale import j
import textwrap
from copy import deepcopy
app = j.tools.prefab._BaseAppClass

compileconfig = {}
compileconfig['enable_mbstring'] = True
compileconfig['enable_zip'] = True
compileconfig['with_gd'] = True
compileconfig['with_curl'] = True  # apt-get install libcurl4-openssl-dev libzip-dev
compileconfig['with_libzip'] = True
compileconfig['with_zlib'] = True
compileconfig['with_openssl'] = True
compileconfig['enable_fpm'] = True
compileconfig['prefix'] = "{DIR_BASE}/apps/php"
compileconfig['exec_prefix'] = "{DIR_BASE}/apps/php"
compileconfig['with_mysqli'] = True
compileconfig['with_pdo_mysql'] = True
compileconfig['with_mysql_sock'] = "/var/run/mysqld/mysqld.sock"


class PrefabPHP(app):

    NAME = 'php'

    def build(self, **config):

        pkgs = "libxml2-dev libpng-dev libcurl4-openssl-dev libzip-dev zlibc zlib1g zlib1g-dev libmysqld-dev libmysqlclient-dev re2c bison bzip2 build-essential libaprutil1-dev libapr1-dev openssl pkg-config libssl-dev libsslcommon2-dev file"
        list(map(self.prefab.system.package.ensure, pkgs.split(sep=" ")))

        compileconfig['with_apxs2'] = self.prefab.core.replace("{DIR_BASE}/apps/apache2/bin/apxs")
        buildconfig = deepcopy(compileconfig)
        buildconfig.update(config)  # should be defaultconfig.update(config) instead of overriding the explicit ones.

        # check for apxs2 binary if it's valid.
        apxs = buildconfig['with_apxs2']
        if not self.prefab.core.file_exists(apxs):
            buildconfig.pop('with_apxs2')

        args_string = ""
        for k, v in buildconfig.items():
            k = k.replace("_", "-")
            if v is True:
                args_string += " --{k}".format(k=k)
            else:
                args_string += " --{k}={v}".format(k=k, v=v)
        C = """
        set -x
        rm -f {DIR_TEMP}/php-7.0.17.tar.bz*
        cd {DIR_TEMP} && [ ! -f {DIR_TEMP}/php-7.0.17.tar.bz2 ] && wget http://be2.php.net/distributions/php-7.0.17.tar.bz2
        cd {DIR_TEMP} && tar xvjf {DIR_TEMP}/php-7.0.17.tar.bz2
        mv {DIR_TEMP}/php-7.0.17/ {DIR_TEMP}/php

        """

        C = self.executor.replace(C)
        self.prefab.core.run(C)

        C = """cd {DIR_TEMP}/php && ./configure {args_string}""".format(args_string=args_string)
        self.prefab.core.run(C, die=False)

        C = """cd {DIR_TEMP}/php && make"""
        self.prefab.core.run(C, die=False)

        # check if we need an php accelerator: https://en.wikipedia.org/wiki/List_of_PHP_accelerators

    def install(self, start=False):
        fpmdefaultconf = """\
        include={DIR_BASE}/apps/php/etc/php-fpm.d/*.conf
        """
        fpmwwwconf = """\
        ;nobody Start a new pool named 'www'.
        [www]

        ;prefix = /path/to/pools/$pool

        user =  www-data
        group = www-data

        listen = 127.0.0.1:9000

        listen.allowed_clients = 127.0.0.1

        pm = dynamic
        pm.max_children = 5
        pm.start_servers = 2
        pm.min_spare_servers = 1
        pm.max_spare_servers = 3
        """
        fpmdefaultconf = textwrap.dedent(fpmdefaultconf)
        fpmwwwconf = textwrap.dedent(fpmwwwconf)
        # make sure to save that configuration file ending with .conf under php/etc/php-fpm.d/www.conf
        C = """
        cd {DIR_TEMP}/php && make install
        """

        C = self.executor.replace(C)
        self.prefab.core.run(C)
        fpmdefaultconf = self.executor.replace(fpmdefaultconf)
        fpmwwwconf = self.executor.replace(fpmwwwconf)
        self.prefab.core.file_write("{DIR_BASE}/apps/php/etc/php-fpm.conf.default", content=fpmdefaultconf)
        self.prefab.core.file_write("{DIR_BASE}/apps/php/etc/php-fpm.d/www.conf", content=fpmwwwconf)
        self.prefab.bash.profileJS.addPath(self.executor.replace('{DIR_BASE}/apps/php/bin'))
        self.prefab.bash.profileJS.save()

        # FOR APACHE
        self.prefab.core.dir_ensure('{DIR_BASE}/apps/php/lib/')
        self.prefab.core.file_copy("{DIR_TEMP}/php/php.ini-development", "{DIR_BASE}/apps/php/lib/php.ini")
        if start:
            self.start()

    def start(self):
        phpfpmbinpath = '{DIR_BASE}/apps/php/sbin'
        # COPY BINARIES
        self.prefab.core.run("cp {DIR_BASE}/apps/php/sbin/* {DIR_BIN}")

        phpfpmcmd = "{DIR_BASE}/apps/php/sbin/php-fpm -F -y {DIR_BASE}/apps/php/etc/php-fpm.conf.default"  # foreground
        phpfpmcmd = self.executor.replace(phpfpmcmd)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(name="php-fpm", cmd=phpfpmcmd, path=phpfpmbinpath)

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("php-fpm")

    def test(self):
        # TODO: *2 test php deployed in nginx
        # check there is a local nginx running, if not install it
        # deploy some php script, test it works
        raise NotImplementedError
