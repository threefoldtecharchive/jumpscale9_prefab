from jumpscale import j


app = j.tools.prefab._getBaseAppClass()


class PrefabVirtualBox(app):
    NAME = "virtualbox"

    def install(self, reset=False):

        from IPython import embed
        self.logger.info("DEBUG NOW virtualbox")
        embed()
        raise RuntimeError("stop debug here")
