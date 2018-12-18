from Jumpscale import j


app = j.tools.prefab._BaseAppClass


class PrefabVirtualBox(app):
    NAME = "virtualbox"

    def install(self, reset=False):

        from IPython import embed
        self._logger.info("DEBUG NOW virtualbox")
        embed()
        raise RuntimeError("stop debug here")
