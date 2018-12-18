from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabWeave(app):
    """
    virtual network services for docker
    """
    NAME = "weave"

    def _install(self, jumpscalePath=True, reset=False):
        if reset is False and self.isInstalled():
            return
        if jumpscalePath:
            binPath = self.prefab.core.joinpaths(
                '{DIR_BIN}', 'weave')
        else:
            binPath = '/usr/local/bin/weave'
        self.prefab.core.dir_ensure(j.sal.fs.getParent(binPath))

        C = '''
        curl -L git.io/weave -o {binPath} && sudo chmod a+x {binPath}
        '''.format(binPath=binPath)
        C = self.executor.replace(C)
        self.prefab.systemservices.docker.install()
        self.prefab.system.package.ensure('curl')
        self.prefab.core.execute_bash(C, profile=True)
        self.prefab.bash.addPath(j.sal.fs.getParent(binPath))

    def install(self, start=True, peer=None, jumpscalePath=True, reset=False):
        self._install(jumpscalePath=jumpscalePath, reset=reset)
        if start:
            self.start(peer)

    def start(self, peer=None):
        rc, out, err = self.prefab.core.run("weave status", profile=True, die=False, showout=False)
        if rc != 0:
            cmd = 'weave launch'
            if peer:
                cmd += ' %s' % peer
            self.prefab.core.run(cmd, profile=True)

        _, env, _ = self.prefab.core.run('weave env', profile=True)
        ss = env[len('export'):].strip().split(' ')
        for entry in ss:
            splitted = entry.split('=')
            if len(splitted) == 2:
                # TODO: it will creash if a the machine is restarted cause weave socket doesn't exist
                self.prefab.bash.envSet(splitted[0], splitted[1])
            elif len(splitted) > 0:
                self.prefab.bash.envSet(splitted[0], '')
