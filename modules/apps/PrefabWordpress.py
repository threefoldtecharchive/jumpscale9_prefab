from js9 import j
import textwrap

app = j.tools.prefab._getBaseAppClass()


class PrefabWordpress(app):
    NAME = "wordpress"

    def _init(self):
        self.user = "wordpress"
        self.path = "/opt/var/data/www"

    def build(self, reset=False):
        """
        build wordpress
        1- install php
        2- install mysql
        3- install caddy
        4- install wp-cli (a cli tool for wordpress)
        """
        if self.doneCheck("build", reset):
            return
        # 1- install php
        self.prefab.system.package.install(
            "php7.0-fpm, php7.0-mysql, php7.0-curl, php7.0-gd, php7.0-mbstring, php7.0-mcrypt, php7.0-xml, php7.0-xmlrpc")

        # 2- install mysql
        self.prefab.db.mariadb.install()

        # 3- install caddy
        self.prefab.web.caddy.install(plugins=["iyo"])

        #4- nstall wp-cli
        url = "https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
        cli_path = "/usr/local/bin/wp"
        cli_path = self.replace(cli_path)
        self.prefab.core.file_download(url=url, to=cli_path, overwrite=True, retry=3, timeout=0, removeTopDir=False)

        self.prefab.executor.execute('chmod +x %s' % cli_path)
        if not self.prefab.system.user.check(self.user):
            self.prefab.system.user.create(self.user)
        self.doneSet("build")

    def install(self, url, title, admin_user, admin_password, admin_email, 
                db_name, db_user, db_password, port=8090, plugins=None, reset=False):
        """install 
        """
        if self.doneCheck("install", reset):
            return
        self.build(reset=reset)
        
        # create a database 
        self.prefab.db.mariadb.sql_execute("CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" % db_name)
        # create a new super user for this database
        self.prefab.db.mariadb.admin_create(db_user, db_password, db_name= db_name)
        
        self.prefab.core.dir_ensure(self.path)
        self.prefab.core.run("chown {0}:{0} {1}".format(self.user, self.path))

        # start server
        cfg = """
        :{} {{
           	bind 0.0.0.0
        	root {}
           	fastcgi / /var/run/php/php7.0-fpm.sock php
        }}
        """.format(port, self.path)
        self.prefab.web.caddy.add_website("wordpress",cfg)

        self.prefab.executor.execute("rm -rf {}/*".format(self.path))
        # download wordpress
        self.prefab.executor.execute("sudo -u {} -i -- wp core download --path={}".format(self.user, self.path))

        # configure wordpress
        configure_command = """
        sudo -u {user} -i -- wp --path={path} config create --dbname={db_name} --dbuser='{db_user}' --dbpass='{db_password}' 
        """.format(user=self.user, db_name=db_name, db_user=db_user, db_password=db_password, path=self.path)
        self.prefab.executor.execute(configure_command)

        # install wordpress
        install_command = """
        sudo -u {user} -i -- wp  --path={path} core install --url='{url}' --title='{title}' --admin_user='{admin_user}' --admin_password='{admin_password}' --admin_email='{admin_email}'
        """.format(user=self.user, url=url, title=title, admin_user=admin_user, 
                   admin_password=admin_password, admin_email=admin_email, path=self.path)
        self.prefab.executor.execute(install_command)
        
        # install plugins
        if not plugins:
            plugins = []
        
        for plugin in plugins:
            plugins_command = """
            sudo -u {} -i -- wp --path={} plugin install {}
            """.format(self.user, self.path, plugin)
            self.prefab.core.run(plugins_command, die=False)

        
        self.doneSet("install")


    