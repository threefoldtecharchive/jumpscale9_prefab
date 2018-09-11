import urllib3
from Jumpscale import j


base = j.tools.prefab._getBaseClass()


class PrefabGit(base):

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get("prefab.git")
        return self._logger

    def build(self):
        """
        pull repo of git code & build git command line, goal is to have smallest possible git binary
        """
        self.prefab.system.package.install([
            "tcl",
            "libcurl4-gnutls-dev",
            "gettext",
            "libssl-dev",
        ])

        path = self.pullRepo(url="https://github.com/git/git.git")
        self.prefab.core.run('cd {} && make install'.format(path))

    def pullRepo(self, url, dest=None, login=None, passwd=None, depth=None,
                 ignorelocalchanges=True, reset=False, branch=None, tag=None, revision=None, ssh=False):

        """
        ssh = if True will build ssh url, if "auto" or "first" will check if there is ssh-agent available & keys are loaded,
            if yes will use ssh (True)
            if no will use http (False)
        """

        if dest is None:
            _, _, _, _, dest, url, _ = j.clients.git.getGitRepoArgs(
                url, dest, login, passwd, reset=reset, ssh=ssh, codeDir=self.prefab.core.dir_paths["CODEDIR"])
            # we need to work in remote linux so we only support /opt/code
        else:
            dest = self.replace(dest)

        self.prefab.core.dir_ensure(j.sal.fs.getParent(dest))

        parsed_url = urllib3.util.parse_url(url)
        if parsed_url.scheme in ('ssh', 'git'):
            self.prefab.core.dir_ensure('$HOMEDIR/.ssh')
            keys = self.prefab.core.run("ssh-keyscan -H -p %s %s" % (parsed_url.port or 22, parsed_url.host))[1]
            self.prefab.core.dir_ensure('$HOMEDIR/.ssh')
            known_hosts = "$HOMEDIR/.ssh/known_hosts"
            if self.prefab.core.exists(known_hosts):
                known_hosts_lines = set(self.prefab.core.file_read("$HOMEDIR/.ssh/known_hosts").splitlines())
                keys = set(keys.splitlines())
                keys_to_add = "\n".join(known_hosts_lines.union(keys))
            else:
                keys_to_add = keys
            self.prefab.core.file_append("$HOMEDIR/.ssh/known_hosts", keys_to_add)
            self.prefab.core.file_attribs("$HOMEDIR/.ssh/known_hosts", mode=600)

        self.logger.info("pull %s with depth:%s" % (url, depth))

        return j.clients.git.pullGitRepo(url=url, dest=dest, login=login, passwd=passwd, depth=depth,
                                ignorelocalchanges=ignorelocalchanges, reset=reset, branch=branch, revision=revision,
                                ssh=ssh, executor=self.executor, tag=tag)
