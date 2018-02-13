from js9 import j
import textwrap

app = j.tools.prefab._getBaseAppClass()


class PrefabWordpress(app):
    NAME = "wordpress"

    def _init(self):
        pass

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
        self.prefab.web.caddy.install()

        #4- nstall wp-cli
        url = "https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar"
        cli_path = "{{TMPDIR}}/wp-cli.phar"
        cli_path = self.replace(cli_path)
        self.prefab.core.file_download(url=url, to=cli_path, overwrite=True, retry=3, timeout=0, expand=True, removeTopDir=False)
        self.prefab.executor.execute('chmod +x %s' % cli_path)
        j.sal.fs.moveFile(cli_path, '/usr/local/bin/wp')

        self.doneSet("build")

    def install(self, url, title, admin_user, admin_password, admin_email, db_name, db_user, db_password, reset=False):
        """install 
        """
        if self.doneCheck("install", reset):
            return
        self.build(reset=reset)
        
        # create a database 
        self.prefab.db.mariadb.sql_execute("CREATE DATABASE %s DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" % db_name)
        # create a new super user for this database
        self.prefab.db.mariadb.admin_create(db_user, db_password, db_name= db_name)
        
        self.prefab.core.dir_ensure('/opt/var/data/www')

        #start webserver here
        

        self.prefab.executor.execute("wp core download --path=/opt/var/data/www")
        install_command = """
        wp core install --url={url} --title={title} --admin_user={admin_user}
         --admin_password={admin_password} --admin_email={admin_email}
        """.format(url=url, title=title, admin_user=admin_user, admin_password=admin_password, admin_email=admin_email)
        self.prefab.executor.execute(install_command)

        configure_command = """
        wp config create --dbname={db_name} --dbuser={db_user} --dbpass={db_password}
        """.format(db_name=db_name, db_user=db_user, db_password=db_password)
        self.prefab.executor.execute(install_command)

        #will add more plugins here
        plugins_command = """
        wp plugin install bbpress
        """
        self.prefab.executor.execute(install_command)

        
        self.doneSet("install")


    