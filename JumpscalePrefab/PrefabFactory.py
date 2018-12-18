from Jumpscale import j
from JumpscalePrefab.PrefabBase import *

from JumpscalePrefab.PrefabLoader import PrefabLoader

JSBASE = j.application.JSBaseClass


class PrefabRootClassFactory(JSBASE):

    prefabs_instance = {}
    _local = None

    def __init__(self):
        self.__jslocation__ = "j.tools.prefab"
        JSBASE.__init__(self)
        self._local = None
        self.loader = PrefabLoader()

    @property
    def local(self):
        if self._local is None:
            self._local = self.get(j.tools.executorLocal)
        return self._local

    @property
    def _BaseClass(self):
        return PrefabBase

    @property
    def _BaseAppClass(self):
        return PrefabApp

    def reset(self, prefab):
        """
        reset remove the prefab instance passed in argument from the cache.
        """
        if prefab.executor.id in self.prefabs_instance:
            del self.prefabs_instance[prefab.executor.id]

    def resetAll(self):
        """
        reset cache of prefab instances
        """
        self.prefabs_instance = {}

    def get_pubkey(self, keyname=''):
        if keyname == '':
            return self._generate_pubkey()

        key = j.clients.ssh.sshkey_path_get(keyname)
        return j.sal.fs.readFile(key + '.pub')

    def _get_ssh_executor(self, addr, port, login, passphrase, passwd):
        if not passwd and passphrase is not None:
            return j.tools.executor.getSSHBased(addr=addr,
                                                port=port,
                                                login=login,
                                                passphrase=passphrase)
        else:
            passwd = passwd if passwd else j.tools.console.askPassword("please specify root passwd", False)
            return j.tools.executor.getSSHBased(addr=addr,
                                                port=port,
                                                login=login,
                                                passwd=passwd)

    def getFromSSH(self, addr, port=22, login='root'):
        instance = '{0}:{1}'.format(addr, port)
        data = {
            'addr': addr,
            'port': port,
            'login': login
        }
        sshclient = j.clients.ssh.get(instance, data)
        e = j.tools.executor.ssh_get(sshclient)
        return self.get(executor=e)

    def get(self, executor=None, usecache=True):
        """
        example:
        executor=j.tools.executor.getSSHBased(addr='localhost', port=22,login="root",
                                              passwd="1234",pushkey="ovh_install")
        prefab=j.tools.prefab.get(executor)

        executor can also be a string like: 192.168.5.5:9022

        or if used without executor then will be the local one
        """
        from JumpscalePrefab.PrefabRootClass import PrefabRootClass

        if usecache and executor.id in self.prefabs_instance:
            return self.prefabs_instance[executor.id]

        prefab = PrefabRootClass(executor)

        self.loader.load(executor, prefab)

        self.prefabs_instance[executor.id] = prefab

        return self.prefabs_instance[executor.id]

    def getFromId(self, id):
        executor = j.tools.executor.get(id)
        return self.get(executor)

    def test(self, executor=None):
        """
        executor can be a real executor or a hostname e.g. ovh4:22

        js_shell 'j.tools.prefab.test()'

        """
        if j.data.types.string.check(executor):
            c = j.tools.prefab.get(executor)
            e = c.executor
            assert e.prefab == c
        elif executor is None:
            e = j.tools.executorLocal

        c = e.prefab.apps.gogs

        c.doneReset()

        c.doneSet("test")
        assert c.doneGet("test")

        c.doneReset()
        assert c.doneGet("test")==False

        print ("TEST OK")

