from js9 import j
import textwrap

app = j.tools.prefab._getBaseAppClass()


class PrefabWordpress(app):
    NAME = "wordpress"

    def _init(self):
        self.user = "wordpress"

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
        self.prefab.db.mariadb.install(start=True)

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

    def install(self, path, url, title, admin_user, admin_password, admin_email, 
                db_name='wordpress', db_user='wordpress', db_password='wordpress', port=8090, plugins=None, theme=None, reset=False):
        """install 

        @param path: a path to setup wordpress to, Note that all content in this path will be deleted
        @param url: website's url
        @param title: website's title
        @param admin_user: admin username
        @param admin_password: admin password
        @param admin_email: admin email
        @param db_name: (default = Wordpress) database name to be used in wordpress
        @param db_user: (default = wordpress) database user 
        @param db_password: (default = wordpress) database password, Very important to change with a strong password
        @param port: (default = 8090) the host port
        @param plugins: (default = None) list of plugin names you want to install, Acceps plugins slugs from 
        wordpress plugins directory: https://wordpress.org/plugins/
        @param reset: (default = False) if True build will start again even if it was already built
        """
        if self.doneCheck("install", reset):
            return
        self.build(reset=reset)
        
        # create a database 
        self.prefab.db.mariadb.sql_execute(None, "CREATE DATABASE IF NOT EXISTS %s DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" % db_name)
        # create a new super user for this database
        self.prefab.db.mariadb.admin_create(db_user, db_password)
        
        self.prefab.core.dir_ensure(path)
        self.prefab.core.run("chown {0}:{0} {1}".format(self.user, path))

        # start server
        cfg = """
        :{} {{
           	bind 0.0.0.0
        	root {}
           	fastcgi / /var/run/php/php7.0-fpm.sock php
        }}
        """.format(port, path)
        self.prefab.web.caddy.add_website("wordpress",cfg)

        self.prefab.executor.execute("rm -rf {}/*".format(path))
        # download wordpress
        self.prefab.executor.execute("sudo -u {} -i -- wp core download --path={}".format(self.user, path))

        # configure wordpress
        configure_command = """
        sudo -u {user} -i -- wp --path={path} config create --dbname={db_name} --dbuser='{db_user}' --dbpass='{db_password}' 
        """.format(user=self.user, db_name=db_name, db_user=db_user, db_password=db_password, path=path)
        self.prefab.executor.execute(configure_command)

        # install wordpress
        #TODO:*1 why like this with sudo?
        install_command = """
        sudo -u {user} -i -- wp  --path={path} core install --url='{url}' --title='{title}' --admin_user='{admin_user}' --admin_password='{admin_password}' --admin_email='{admin_email}'
        """.format(user=self.user, url=url, title=title, admin_user=admin_user, 
                   admin_password=admin_password, admin_email=admin_email, path=path)
        self.prefab.executor.execute(install_command)
        
        # install themes
        self.install_theme(path, theme)

        # install plugins
        self.install_plugins(path, plugins)

        
        self.doneSet("install")

    def install_theme(self, path, theme):
        if theme:
            themes_command = """
            sudo -u {} -i -- wp --path={} theme install {} --activate
            """.format(self.user, path, theme)
            self.prefab.core.run(themes_command, die=False)

    def install_plugins(self, path, plugins):
        if not plugins:
            plugins = []
        
        for plugin in plugins:
            plugins_command = """
            sudo -u {} -i -- wp --path={} plugin install {}
            """.format(self.user, path, plugin)
            self.prefab.core.run(plugins_command, die=False)
