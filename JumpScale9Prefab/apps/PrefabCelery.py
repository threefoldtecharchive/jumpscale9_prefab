from js9 import j

base = j.tools.prefab._getBaseAppClass()

class PrefabCelery(base):

    def _init(self):
        self.code_dir = '/opt/code/github/jumpscale/srobot'

    def install(self):
        self.prefab.development.pip.install('celery[redis]')
        self.prefab.development.pip.install('flower')
        j.clients.git.pullGitRepo(url='git@github.com:Jumpscale/srobot.git')
        j.clients.redis.start4core()

    def start(self):
        cmd = 'celery -A tasks worker --loglevel=info'
        self.prefab.processmanager.ensure('celery1', cmd=cmd, path=self.code_dir)
        cmd = 'celery -A tasks flower --address=0.0.0.0 --port=5555 --broker=redis://localhost:6379'
        self.prefab.processmanager.ensure('celery2', cmd=cmd, path=self.code_dir)
