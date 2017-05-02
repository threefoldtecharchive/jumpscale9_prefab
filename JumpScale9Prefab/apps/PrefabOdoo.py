from js9 import j

app = j.tools.prefab._getBaseAppClass()


class PrefabOdoo(app):
    NAME = "odoo-bin"

    def _group_exists(self, groupname):
        return groupname in open("/etc/group").read()

    def _install_pip(self):
        self.prefab.core.run('apt-get --assume-yes install python2.7 python2.7-dev')
        cmd = """
        cd $TMPDIR
        wget https://bootstrap.pypa.io/get-pip.py
        python2.7 get-pip.py
        """
        self.prefab.core.execute_bash(cmd, profile=True)

    def build(self):
        if not self.prefab.apps.postgresql.isInstalled():
            self.prefab.apps.postgresql.build()
            self.prefab.apps.postgresql.install()
        self._install_pip()
        cmd = """
        cd $TMPDIR && git clone https://github.com/odoo/odoo.git --depth=1
        export PATH=$PATH:$BINDIR/postgres/
        apt-get -y install python-ldap libldap2-dev libsasl2-dev libssl-dev libxml2-dev libxslt-dev python-dev
        cd $TMPDIR/odoo && pip2 install -r requirements.txt
        """
        self.prefab.core.run(cmd, profile=True)

    def install(self):
        if not self.prefab.apps.postgresql.isStarted():
            self.prefab.apps.postgresql.start()
        if not self._group_exists("odoo"):
            self.prefab.core.run('adduser --system --quiet  \
        --shell /bin/bash --group --gecos "Odoo administrator" odoo')
            self.prefab.core.run('sudo -u postgres $BINDIR/createuser -s odoo')

        c = """
        cp $TMPDIR/odoo/odoo-bin $BINDIR/odoo-bin
        cp -r $TMPDIR/odoo/odoo $JSLIBEXTDIR
        cp -r $TMPDIR/odoo/addons $JSLIBEXTDIR/odoo-addons
        """
        self.prefab.core.run(c, profile=True)

    def start(self):
        if not self.prefab.apps.postgresql.isStarted():
            self.prefab.apps.postgresql.start()
        cmd = """
        cd $BINDIR
        sudo -H -u odoo PYTHONPATH=$JSLIBEXTDIR:$PYTHONPATH LD_LIBRARY_PATH=$LIBDIR/postgres/:$LD_LIBRARY_PATH ./odoo-bin --addons-path=$JSLIBEXTDIR/odoo-addons,$JSLIBEXTDIR/odoo/addons/
        """
        self.prefab.core.execute_bash(cmd, profile=True)
