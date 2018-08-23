from jumpscale import j
import os
import textwrap
from time import sleep


app = j.tools.prefab._getBaseAppClass()


class PrefabNGINX(app):
    NAME = 'nginx'

    def _init(self):
        self.BUILDDIR = self.replace("$BUILDDIR")

    def get_basic_nginx_conf(self):
        return """\
        user www-data;
        worker_processes auto;
        pid /run/nginx.pid;

        events {
        	worker_connections 768;
        	# multi_accept on;
        }

        http {

        	##
        	# Basic Settings
        	##

        	sendfile on;
        	tcp_nopush on;
        	tcp_nodelay on;
        	keepalive_timeout 65;
        	types_hash_max_size 2048;
        	# server_tokens off;

        	# server_names_hash_bucket_size 64;
        	# server_name_in_redirect off;

        	include $BUILDDIR/nginx/conf/mime.types;
        	default_type application/octet-stream;

        	##
        	# SSL Settings
        	##

        	ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
        	ssl_prefer_server_ciphers on;

        	##
        	# Logging Settings
        	##

        	access_log $BUILDDIR/nginx/logs/access.log;
        	error_log $BUILDDIR/nginx/logs/error.log;

        	##
        	# Gzip Settings
        	##

        	gzip on;
        	gzip_disable "msie6";

        	##
        	# Virtual Host Configs
        	##

        	include $BUILDDIR/nginx/conf/conf.d/*;
        	include $BUILDDIR/nginx/conf/sites-enabled/*;
        }
        """

    def get_basic_nginx_site(self, wwwPath="/var/www/html"):
        return """\
        server {
            listen 80 default_server;
            listen [::]:80 default_server;

            root %s;

            # Add index.php to the list if you are using PHP
            index index.html index.htm index.nginx-debian.html index.php;

            server_name _;

            location / {
                # First attempt to serve request as file, then
                # as directory, then fall back to displaying a 404.
                try_files $uri $uri/ =404;
            }

            # location ~ \.php$ {
                # include $BUILDDIR/nginx/conf/snippets/fastcgi-php.conf;

                # With php7.0-cgi alone:
                # fastcgi_pass 127.0.0.1:9000;
            # With php7.0-fpm:
                # fastcgi_pass unix:/run/php/php7.0-fpm.sock;
            # }
        }
        """ % wwwPath

    def install(self, start=True):
        """
        Moving build files to build directory and copying config files
        """

        """
        # Install through ubuntu
        # self.prefab.system.package.mdupdate()
        # self.prefab.system.package.ensure('nginx')
        # link nginx to binDir and use it from there

        # self.prefab.core.dir_ensure("$JSAPPSDIR/nginx/")
        # self.prefab.core.dir_ensure("$JSAPPSDIR/nginx/bin")
        # self.prefab.core.dir_ensure("$JSAPPSDIR/nginx/etc")
        self.prefab.core.dir_ensure("$JSCFGDIR")
        self.prefab.core.dir_ensure("$TMPDIR")
        # self.prefab.core.dir_ensure("/optvar/tmp")
        self.prefab.core.dir_ensure("$JSAPPSDIR/nginx/")
        self.prefab.core.dir_ensure("$JSAPPSDIR/nginx/bin")
        self.prefab.core.dir_ensure("$JSAPPSDIR/nginx/etc")
        self.prefab.core.dir_ensure("$JSCFGDIR/nginx/etc")

        self.prefab.core.file_copy('/usr/sbin/nginx', '$JSAPPSDIR/nginx/bin/nginx', overwrite=True)
        self.prefab.core.dir_ensure('/var/log/nginx')
        self.prefab.core.file_copy('/etc/nginx/*', '$JSAPPSDIR/nginx/etc/', recursive=True)  # default conf
        self.prefab.core.file_copy('/etc/nginx/*', '$JSCFGDIR/nginx/etc/', recursive=True)  # variable conf
        """

        # Install nginx

        C = """
        #!/bin/bash
        set -ex

        cd $TMPDIR/build/nginx/nginx-1.11.3
        make install
        """

        C = self.prefab.core.replace(C)
        C = self.replace(C)
        self.prefab.core.run(C)

        # Writing config files
        self.prefab.core.dir_ensure("$BUILDDIR/nginx/conf/conf.d/")
        self.prefab.core.dir_ensure("$BUILDDIR/nginx/conf/sites-enabled/")

        basicnginxconf = self.get_basic_nginx_conf()
        basicnginxconf = self.replace(textwrap.dedent(basicnginxconf))

        defaultenabledsitesconf = self.get_basic_nginx_site()
        defaultenabledsitesconf = self.replace(textwrap.dedent(defaultenabledsitesconf))

        self.prefab.core.file_write("$BUILDDIR/nginx/conf/nginx.conf", content=basicnginxconf)
        self.prefab.core.file_write("$BUILDDIR/nginx/conf/sites-enabled/default", content=defaultenabledsitesconf)

        fst_cgi_conf = self.prefab.core.file_read("$BUILDDIR/nginx/conf/fastcgi.conf")
        fst_cgi_conf = fst_cgi_conf.replace("include fastcgi.conf;",
                                            self.replace("include $BUILDDIR/nginx/conf/fastcgi.conf;"))
        self.prefab.core.file_write("$BUILDDIR/nginx/conf/fastcgi.conf", content=fst_cgi_conf)

        #self.prefab.core.file_link(source="$JSCFGDIR/nginx", destination="$JSAPPSDIR/nginx")
        if start:
            self.start()

    def build(self, install=True):
        self.prefab.bash.locale_check()

        if self.prefab.core.isUbuntu:
            self.prefab.system.package.mdupdate()
            self.prefab.system.package.install("build-essential libpcre3-dev libssl-dev")

            self.prefab.core.dir_remove("$TMPDIR/build/nginx")
            self.prefab.core.dir_ensure("$TMPDIR/build/nginx")

            C = """
            #!/bin/bash
            set -ex

            cd $TMPDIR/build/nginx
            wget http://nginx.org/download/nginx-1.11.3.tar.gz
            tar xzf nginx-1.11.3.tar.gz

            cd nginx-1.11.3
            ./configure --prefix=$BUILDDIR/nginx/ --with-http_ssl_module --with-ipv6
            make
            """
            C = self.prefab.core.replace(C)
            C = self.replace(C)
            self.prefab.core.run(C)

        else:
            raise j.exceptions.NotImplemented(
                message="only ubuntu supported for building nginx")

        if install:
            self.install()

    def start(self, name="nginx", nodaemon=True, nginxconfpath=None):
        nginxbinpath = '$BUILDDIR/nginx/sbin'
        # COPY BINARIES TO BINDIR
        self.prefab.core.dir_ensure('$BINDIR')
        self.prefab.core.run("cp $BUILDDIR/nginx/sbin/* $BINDIR/")

        if nginxconfpath is None:
            nginxconfpath = '$BUILDDIR/nginx/conf/nginx.conf'

        nginxconfpath = self.replace(nginxconfpath)
        nginxconfpath = os.path.normpath(nginxconfpath)

        if self.prefab.core.file_exists(nginxconfpath):
            # foreground
            nginxcmd = "%s/nginx -c %s -g 'daemon off;'" % (nginxbinpath, nginxconfpath)
            nginxcmd = self.replace(nginxcmd)

            self.logger.info("cmd: %s" % nginxcmd)
            pm = self.prefab.system.processmanager.get()
            pm.ensure(name=name, cmd=nginxcmd, path=nginxbinpath)

        else:
            raise RuntimeError('Failed to start nginx')

    def stop(self):
        pm = self.prefab.system.processmanager.get()
        pm.stop("nginx")

    def test(self):
        # host a file test can be reached
        raise NotImplementedError
