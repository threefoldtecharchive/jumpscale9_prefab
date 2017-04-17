
from JumpScale import j

base = j.tools.cuisine._getBaseClass()


class CuisineDropbear(base):

    def build(self):
        url = "https://matt.ucc.asn.au/dropbear/releases/dropbear-2016.74.tar.bz2"
        from IPython import embed
        self.logger.info("DEBUG NOW uuuy")
        embed()
        raise RuntimeError("stop debug here")
