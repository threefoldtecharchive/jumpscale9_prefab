
from JumpScale import j


base = j.tools.cuisine._getBaseClass()


class CuisineGit(base):

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get("cuisine.git")
        return self._logger

    def build(self):
        """
        pull repo of git code & build git command line, goal is to have smallest possible git binary
        """
        self.cuisine.package.multiInstall([
            "tcl",
            "libcurl4-gnutls-dev",
            "gettext",
            "libssl-dev",
        ])

        path = self.pullRepo(url="https://github.com/git/git.git")
        self.cuisine.core.run('cd {} && make install'.format(path))

    def pullRepo(self, url, dest=None, login=None, passwd=None, depth=None,
                 ignorelocalchanges=True, reset=False, branch=None, tag=None, revision=None, ssh="first"):

        if dest is None:
            base, provider, account, repo, dest, url = j.do.getGitRepoArgs(
                url, dest, login, passwd, reset=reset, ssh=ssh, codeDir=self.cuisine.core.dir_paths["CODEDIR"])
            # we need to work in remote linux so we only support /opt/code
        else:
            dest = self.replace(dest)

        self.cuisine.core.dir_ensure(j.sal.fs.getParent(dest))
        self.cuisine.core.dir_ensure('$HOMEDIR/.ssh')
        keys = self.cuisine.core.run("ssh-keyscan -H github.com")[1]
        self.cuisine.core.dir_ensure('$HOMEDIR/.ssh')
        self.cuisine.core.file_append("$HOMEDIR/.ssh/known_hosts", keys)
        self.cuisine.core.file_attribs("$HOMEDIR/.ssh/known_hosts", mode=600)

        self.logger.info("pull %s with depth:%s" % (url, depth))

        return j.do.pullGitRepo(url=url, dest=dest, login=login, passwd=passwd, depth=depth,
                                ignorelocalchanges=ignorelocalchanges, reset=reset, branch=branch, revision=revision,
                                ssh=ssh, executor=self.executor, tag=tag)
