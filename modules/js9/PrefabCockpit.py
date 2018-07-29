from jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabCockpit(base):

    def install(self, start=True, branch="master", reset=False, ip="localhost", production=False,
                client_id='', ays_secret='', portal_secret='', organization=''):
        """
        production: cockpit mode (atyourservice and portal in development mode if False)
        client_id: oauth client id
        ays_secret: client secret of ays
        portal_secret: client secret of portal
        organization: oauth organization
        """

        # install portal
        self.prefab.apps.portal.install(start=False, branch=branch, reset=reset)
        # add link from portal to API
        content = self.prefab.core.file_read('$CODEDIR/github/threefoldtech/jumpscale_portal9/apps/portalbase/AYS/.space/nav.wiki')
        content = content.replace('AYS API:http://localhost:5000', "AYS API:http://{ip}:5000".format(ip=ip))
        self.prefab.core.dir_ensure('$JSAPPSDIR/portals/main/base/AYS/.space/')
        self.prefab.core.file_write('$JSAPPSDIR/portals/main/base/AYS/.space/nav.wiki', content=content)

        self.prefab.apps.portal.stop()
        self.prefab.apps.portal.configure(
            production=production,
            client_id=client_id,
            client_secret=portal_secret,
            scope_organization=organization,
            redirect_address='%s:8200' %
            ip)

        # Configure AYS
        # Install ays will just link apidocs, index.html, main.py from $CODEDIR into $JSAPPSDIR
        self.prefab.apps.atyourservice.install()
        self.prefab.apps.atyourservice.stop()
        self.prefab.apps.atyourservice.configure(
            production=production,
            client_secret=ays_secret,
            client_id=client_id,
            organization=organization,
            redirect_address='%s:5000' %
            ip)

        # configure base URI for api-console
        raml_path = "$JSAPPSDIR/atyourservice/JumpscaleAYS/ays/server/apidocs/api.raml"
        raml = self.prefab.core.file_read(raml_path)
        raml = raml.replace('baseUri: https://localhost:5000', "baseUri: http://{ip}:5000".format(ip=ip))
        self.prefab.core.file_write(raml_path, raml)

        if start:
            # start API and daemon
            self.start(host=ip)

    def start(self, host='localhost'):
        # start AYS server
        # start portal
        self.prefab.apps.atyourservice.start(host=host)
        self.prefab.apps.portal.start()

    def stop(self):
        self.prefab.apps.atyourservice.stop()
        self.prefab.apps.portal.stop()

    def install_deps(self):
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.install('libssl-dev')

        deps = """
        cryptography
        python-jose
        wtforms_json
        flask_wtf
        python-telegram-bot
        """
        self.prefab.runtimes.pip.multiInstall(deps, upgrade=True)
