from jumpscale import j

app = j.tools.prefab._getBaseAppClass()


class PrefabLua(app):

    NAME = "lua"

    def package(self, name, server=''):
        if server:
            server = '--server=' + server
        self.prefab.core.run("luarocks install %s %s" % (server, name))
