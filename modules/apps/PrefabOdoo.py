from jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabOdoo(app):
    NAME = "odoo-bin"

    def _install_pip2(self):
        if self.prefab.core.command_check('pip2'):
            return
        pip_url = 'https://bootstrap.pypa.io/get-pip.py'
        self.prefab.system.package.install(['python2.7', 'python2.7-dev'])
        self.prefab.core.file_download(pip_url, overwrite=False)
        cmd = """
        python2.7 $TMPDIR/get-pip.py
        """
        self.prefab.core.execute_bash(cmd, profile=True)

    def build(self):
        if not self.prefab.db.postgresql.isInstalled():
            self.prefab.db.postgresql.install()
        self._install_pip2()
        self.prefab.system.package.install([
            'python-ldap', 'libldap2-dev', 'libsasl2-dev', 'libssl-dev',
            'libxml2-dev', 'libxslt-dev', 'python-six', 'libpq-dev'
        ])
        self.prefab.runtimes.nodejs.install()
        self.prefab.core.run("npm install -g less less-plugin-clean-css -y", profile=True)
        odoo_git_url = "https://github.com/odoo/odoo.git"
        odoo_dir = '$TMPDIR/odoo'
        self.prefab.tools.git.pullRepo(odoo_git_url, dest=odoo_dir, branch='10.0', depth=1, ssh=False)
        cmd = """
        export PATH=$PATH:$BINDIR/postgres/
        cd {} && pip2 install -r requirements.txt
        """.format(odoo_dir)
        self.prefab.core.run(cmd, profile=True)

    def install(self):
        if self.doneGet('install'):
            return
        if not self.doneGet('build'):
            self.build()
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()
        self.prefab.core.run('adduser --system --quiet --shell /bin/bash --group --gecos "Odoo administrator" odoo')
        self.prefab.core.run('sudo -u postgres $BINDIR/createuser -s odoo')
        self.prefab.core.dir_ensure("$JSLIBEXTDIR")

        c = """
        cp $TMPDIR/odoo/odoo-bin $BINDIR/odoo-bin
        cp -r $TMPDIR/odoo/odoo $JSLIBEXTDIR
        cp -r $TMPDIR/odoo/addons $JSLIBEXTDIR/odoo-addons
        """
        self.prefab.core.run(c, profile=True)
        self.doneSet('install')

    def start(self):
        if not self.prefab.db.postgresql.isStarted():
            self.prefab.db.postgresql.start()
        cmd = """
             cd $BINDIR
             sudo -H -u odoo \
             PATH=$PATH \
             PYTHONPATH=$JSLIBEXTDIR:$PYTHONPATH \
             LD_LIBRARY_PATH=$LIBDIR/postgres/:$LD_LIBRARY_PATH \
             ./odoo-bin --addons-path=$JSLIBEXTDIR/odoo-addons,$JSLIBEXTDIR/odoo/addons/ --db-template=template0
        """
        self.prefab.core.execute_bash(cmd, profile=True)
