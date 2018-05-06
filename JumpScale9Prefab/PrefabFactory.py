from js9 import j
from JumpScale9Prefab.PrefabBase import *

from JumpScale9Prefab.PrefabLoader import PrefabLoader

JSBASE = j.application.jsbase_get_class()


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

    def _getBaseClass(self):
        return PrefabBase

    def _getBaseAppClass(self):
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
        return j.sal.fs.fileGetContents(key + '.pub')

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
        from JumpScale9Prefab.PrefabRootClass import PrefabRootClass

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
        """
        if j.data.types.string.check(executor):
            c = j.tools.prefab.get(executor)
            e = c.executor
            assert e.prefab == c
        elif executor is None:
            e = j.tools.executorLocal

        c = e.prefab.apps.alba
        c2 = e.prefab.apps.ipfs

        e.configReset()
        assert e.config == {}

        e.configSet("test", 1)
        assert 1 == e.configGet("test")
        e.configSet("test2", {"a": "bb"})
        assert {"a": "bb"} == e.configGet("test2")

        assert {'test': 1, 'test2': {'a': 'bb'}} == e.config

        e.configReset()
        assert e.config == {}

        c.configReset()
        assert c.config == {}

        c.configSet("test", 1)
        c2.configSet("test", 1)
        assert 1 == c.configGet("test")
        assert 1 == c2.configGet("test")
        c.configSet("test2", {"a": "bb"})
        assert {"a": "bb"} == c.configGet("test2")

        assert {'test': 1, 'test2': {'a': 'bb'}} == c.config

        assert {'PrefabAlba': {'test': 1, 'test2': {'a': 'bb'}}, 'PrefabIPFS': {'test': 1}} == e.config

        # remove all cache
        e.cacheReset()
        assert e._config is None
        assert {'PrefabAlba': {'test': 1, 'test2': {'a': 'bb'}}, 'PrefabIPFS': {'test': 1}} == e.config

        c2.configSet("test", 2)
        e.cacheReset()
        assert 2 == c2.configGet("test")

        c.doneReset()
        assert c.done == {}

        c.doneSet("test")
        assert c.done["test"]

        assert c.doneGet("test")

        e.reset()
        assert c.doneGet("test") == False

        c.doneSet("test")
        assert c.doneGet("test")
        c.configReset()
        assert c.doneGet("test") == False

        c.doneSet("test")
        assert c.doneGet("test")
        c.reset()
        assert c.doneGet("test") == False

        c.doneSet("test")
        assert c.doneGet("test")
        c.cacheReset()
        assert c.doneGet("test")

        assert {'PrefabAlba': {'done': {'test': True}}} == e.config

        # if this takes long & writes long then not ok, need to measure time
        self.logger.info("perf test")
        for i in range(100):
            c.doneGet("test")

        e.reset()
