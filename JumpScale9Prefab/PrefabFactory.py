from js9 import j
import threading
import inspect
from JumpScale9Prefab.PrefabBase import *


class PrefabRootClassFactory:

    _lock = threading.Lock()
    prefabs_instance = {}
    _local = None

    def __init__(self):
        self.__jslocation__ = "j.tools.prefab"
        self.logger = j.logger.get("j.tools.prefab")

    def _getBaseClass(self):
        return PrefabBase

    def _getBaseAppClass(self):
        return PrefabApp

    def _getBaseClassLoader(self):
        return PrefabBaseLoader

    def reset(self, prefab):
        """
        reset remove the prefab instance passed in argument from the cache.
        """
        with self._lock:
            if prefab.executor.id in self.prefabs_instance:
                del self.prefabs_instance[prefab.executor.id]

    def resetAll(self):
        """
        reset cache of prefab isntances
        """
        self.prefabs_instance = {}

    @property
    def local(self):
        with self._lock:
            if self._local is None:
                from JumpScale9Prefab.PrefabRootClass import PrefabRootClass
                self._local = PrefabRootClass(j.tools.executorLocal)
            return self._local

    # def (self):
    #     if not j.do.SSHAgentAvailable():
    #         j.do._loadSSHAgent()
    #     rc, out, err = j.sal.process.execute("ssh-add -l")
    #     keys = []
    #     for line in out.split("\n"):
    #         try:
    #             # TODO: ugly needs to be done better
    #             item = line.split(" ", 2)[2]
    #             keyname = item.split("(", 1)[0].strip()
    #             keys.append(keyname)
    #         except BaseException:
    #             pass
    #     key = j.tools.console.askChoice(keys, "please select key")
    #     # key = j.sal.fs.getBaseName(key)
    #     return j.sal.fs.fileGetContents(key + ".pub")

    def get_pubkey(self, keyname=''):
        if keyname == '':
            return self._generate_pubkey()

        key = j.do.SSHKeyGetPathFromAgent(keyname)
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
        executor = j.tools.executor.get(executor)

        with self._lock:
            if usecache and executor.id in self.prefabs_instance:
                return self.prefabs_instance[executor.id]

            prefab = PrefabRootClass(executor)
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
            c = j.tools.prefab.get("ovh4")
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
