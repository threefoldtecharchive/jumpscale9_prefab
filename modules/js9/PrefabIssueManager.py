from jumpscale import j


base = j.tools.prefab._getBaseClass()


class PrefabIssueManager(base):

    def _init(self):
        self.code_dir = '/opt/code/github/threefoldtech/jumpscale_issue_manager'
        self._logger = j.logger.get('j.prefab.issuemanager')

    def install(self):
        j.clients.git.pullGitRepo(url='git@github.com:Jumpscale/issue_manager.git')
        self.prefab.core.run('cd %s/libs && pip3 install -e .' % self.code_dir)
        self.prefab.core.file_link(source='%s/apps/IssueManager/' % self.code_dir, destination='$JSAPPSDIR/portals/main/base/IssueManager')

    def start(self, passwd=None):
        self.prefab.web.portal.start(passwd)
        self._logger.info("TO CHECK ISSUE MANAGER http://localhost:8200/issuemanager")
