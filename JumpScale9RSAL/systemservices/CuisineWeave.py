from JumpScale import j

app = j.tools.cuisine._getBaseAppClass()


class CuisineWeave(app):
    """
    virtual network services for docker
    """
    NAME = "weave"

    def _install(self, jumpscalePath=True, reset=False):
        if reset is False and self.isInstalled():
            return
        if jumpscalePath:
            binPath = self.cuisine.core.joinpaths(
                self.cuisine.core.dir_paths['BINDIR'], 'weave')
        else:
            binPath = '/usr/local/bin/weave'
        self.cuisine.core.dir_ensure(j.sal.fs.getParent(binPath))

        C = '''
        curl -L git.io/weave -o {binPath} && sudo chmod a+x {binPath}
        '''.format(binPath=binPath)
        C = self.replace(C)
        self.cuisine.systemservices.docker.install()
        self.cuisine.package.ensure('curl')
        self.cuisine.core.execute_bash(C, profile=True)
        self.cuisine.bash.addPath(j.sal.fs.getParent(binPath))

    def install(self, start=True, peer=None, jumpscalePath=True, reset=False):
        self._install(jumpscalePath=jumpscalePath, reset=reset)
        if start:
            self.start(peer)

    def start(self, peer=None):
        rc, out, err = self.cuisine.core.run("weave status", profile=True, die=False, showout=False)
        if rc != 0:
            cmd = 'weave launch'
            if peer:
                cmd += ' %s' % peer
            self.cuisine.core.run(cmd, profile=True)

        _, env, _ = self.cuisine.core.run('weave env', profile=True)
        ss = env[len('export'):].strip().split(' ')
        for entry in ss:
            splitted = entry.split('=')
            if len(splitted) == 2:
                # TODO: it will creash if a the machine is restarted cause weave socket doesn't exist
                self.cuisine.bash.envSet(splitted[0], splitted[1])
            elif len(splitted) > 0:
                self.cuisine.bash.envSet(splitted[0], '')
