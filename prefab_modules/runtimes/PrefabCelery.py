from Jumpscale import j

base = j.tools.prefab._getBaseAppClass()


class PrefabCelery(base):

    def install(self):
        self.prefab.runtimes.pip.install('celery[redis]')
        self.prefab.runtimes.pip.install('flower')
        j.clients.redis.core_get()

    def start(self, cmd, path="{DIR_BASE}/apps/celery/tasks.py", broker='redis://localhost:6379', appname='celery'):
        """
        :param cmd: contains the arg and its parameters, for example `worker --loglevel=info`
        :param path: path of the module defining the celery app, default is {DIR_BASE}/apps/celery/tasks.py
        :param broker: specify the celery broker, default redis
        :param appname: name of celery app
        """
        parent = j.sal.fs.getParent(path)
        module = j.sal.fs.getBaseName(path).split('.py')[0]
        if parent == '{DIR_BASE}/apps/celery' and not self.prefab.core.exists('{DIR_BASE}/apps/celery/tasks.py'):
            content = """
            from celery import Celery
            app = Celery('{name}', broker='{back}', backend='{back}')
            """.format(back=broker, name=appname)
            content = j.core.text.strip(content)
            self.prefab.core.dir_ensure(parent)
            self.prefab.core.file_write(path, content)
        cmd = 'celery -A {module} {cmd} --broker={broker}'.format(module=module, cmd=cmd, broker=broker)
        pm = self.prefab.system.processmanager.get()
        pm.ensure(appname, cmd=cmd, path=parent)
