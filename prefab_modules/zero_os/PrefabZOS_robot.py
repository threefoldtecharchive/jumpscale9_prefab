"""
Module to install 0-robot
"""
from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabZOS_robot(app):
    NAME = "zrobot"
    GITURL = "https://github.com/zero-os/0-robot.git"

    def install(self, branch="master", reset=False):
        """
        Will clone the repository and install the package.

        @param branch: Name of the branch to use when cloning the repository
        @param reset: If True, installation will be re-done
        """
        if self.doneGet('install') and reset is False:
            return

        # clone the repo
        dest = j.clients.git.pullGitRepo(url=self.GITURL, branch=branch, reset=reset, ssh=False)
        j.sal.fs.changeDir(dest)
        # install the package
        j.sal.process.execute("pip3 install -e .")
        self.doneSet('install')
