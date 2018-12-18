
from Jumpscale import j


base = j.tools.prefab._BaseClass


class PrefabMercurial(base):

    def install(self):

        # FIXME: python header files should be included inside /opt as well
        self.prefab.system.package.install("python2.7-dev")
        self.prefab.core.file_download(
            'https://www.mercurial-scm.org/release/mercurial-4.1.tar.gz',
            '{DIR_TEMP}/mercurial-4.1.tar.gz')

        self.prefab.core.run('cd {DIR_TEMP}; tar -xf mercurial-4.1.tar.gz')
        self.prefab.core.run('cd {DIR_TEMP}/mercurial-4.1; python setup.py build')
        # TODO: if BINDIR doesn't end /bin theis won't work
        self.prefab.core.run('cd {DIR_TEMP}/mercurial-4.1; python setup.py install --force')
        # self.prefab.core.run('cd {DIR_TEMP}/mercurial-4.1; python setup.py install --home="{DIR_BIN}/.." --prefix="" --install-lib="$JSLIBEXTDIR" --force')
        self.prefab.core.run("sed -i '1s/python/python2/' {DIR_BIN}/hg")

    def pullRepo(self, url, dest=None,
                 ignorelocalchanges=True, reset=False, branch=None, timeout=1200):

        if not self.prefab.core.command_check("hg"):
            self.install()

        name = j.sal.fs.getBaseName(url)

        if dest is None:
            dest = "{DIR_CODE}/mercurial/%s" % name

        dest = self.executor.replace(dest)

        if reset:
            self.prefab.core.run("rm -rf %s" % dest)

        pdir = j.sal.fs.getParent(dest)

        self._logger.info("mercurial pull %s" % (url))

        if self.prefab.core.dir_exists(dest):
            cmd = "set -ex; cd %s;hg pull %s" % (dest, url)
        else:
            cmd = "set -ex;mkdir -p %s; cd %s;hg clone %s" % (pdir, pdir, url)

        rc, out, err = self.prefab.core.run(cmd)

        return (dest)
