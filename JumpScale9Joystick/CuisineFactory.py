from js9 import j
import threading
import inspect


class CuisineBase:

    def __init__(self, executor, cuisine):
        self._classname = ""
        self._cache = None
        self.executor = executor
        self.cuisine = cuisine
        self._cuisine = cuisine
        self._executor = executor
        self._logger = None
        self.CURDIR = executor.CURDIR
        self.env = executor.env
        if self.classname != 'CuisineCore':
            self.core = cuisine.core
        self._init()

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get(self.classname)
        return self._logger

    def _init(self):
        pass

    def replace(self, txt):
        txt = j.data.text.strip(txt)
        for item in self.__dict__.keys():
            if item == item.upper():
                txt = txt.replace("$%s" % item, self.__dict__[item])
        txt = self.core.replace(txt)
        return txt

    def configReset(self):
        """
        resets config & done memory on node as well as in memory
        """
        if self.classname in self.executor.config:
            self.executor.config.pop(self.classname)
        self.executor.configSave()

    def cacheReset(self):
        self.executor.cacheReset()
        j.data.cache.reset(self.id)

    def reset(self):
        self.configReset()
        self.cacheReset()
        self._init()

    @property
    def config(self):
        """
        is dict which is stored on node itself in msgpack format in /etc/jsexecutor.msgpack
        organized per cuisine module
        """
        if self.classname not in self.executor.config:
            self.executor.config[self.classname] = {}
        return self.executor.config[self.classname]

    def configGet(self, key, defval=None):
        """
        """
        if key in self.config:
            return self.config[key]
        else:
            if defval is not None:
                self.configSet(key, defval)
                return defval
            else:
                raise j.exceptions.Input(message="could not find config key:%s in cuisine:%s" %
                                         (key, self.classname), level=1, source="", tags="", msgpub="")

    def configSet(self, key, val):
        """
        @return True if changed
        """
        if key in self.config:
            val2 = self.config[key]
        else:
            val2 = None
        if val != val2:
            self.executor.config[self.classname][key] = val
            self.logger.debug("config set: %s:%s" % (key, val))
            self.executor.configSave()
            return True
        else:
            self.logger.debug("config not set(was same): %s:%s" % (key, val))
            return False

    @property
    def done(self):
        if "done" not in self.config:
            self.config["done"] = {}
        return self.config["done"]

    def doneReset(self):
        """
        resets the remembered items which are done
        """
        if "done" in self.config:
            self.config.pop("done")
        if not self.executor.readonly:
            self.configSet("done", {})  # this will make sure it gets set remotely

    def doneSet(self, key):
        if self.executor.readonly:
            self.logger.debug("info: Canot do doneset:%s because readonly" % key)
            return False
        self.done[key] = True
        self.executor._config_changed = True
        self.executor.configSave()
        return True

    def doneDelete(self, key):
        if self.executor.readonly:
            self.logger.debug("info: Canot do doneDelete:%s because readonly" % key)
            return False
        self.done[key] = False
        self.executor._config_changed = True
        self.executor.configSave()
        return True

    def doneGet(self, key):
        if self.executor.readonly:
            return False
        if key in self.done:
            self.logger.debug("donecheck:%s:%s" % (key, self.done[key]))
            return self.done[key]
        else:
            self.logger.debug("donecheck, not set:%s:False" % (key))
            return False

    @property
    def classname(self):
        if self._classname == "":
            self._classname = str(self.__class__).split(".")[-1].strip("'>")
        return self._classname

    def reset(self):
        self.cacheReset()
        self.configReset()

    @property
    def id(self):
        return self.executor.id

    @property
    def cache(self):
        if self._cache is None:
            self._cache = j.data.cache.get("cuisine" + self.id + self.classname, reset=True)
        return self._cache

    def __str__(self):
        return "%s:%s" % (self.classname, self.executor.id)

    __repr__ = __str__


class CuisineApp(CuisineBase):

    NAME = None
    VERSION = None

    def isInstalled(self):
        """
        Checks if a package is installed or not
        You can ovveride it to use another way for checking
        """
        return self.cuisine.core.command_check(self.NAME)

    def isStarted(self):
        """
        Checks if a package already started
        You can ovveride it to use another way for checking
        """
        return not self._cuisine.core.run('pgrep %s' % self.NAME, die=False)[0]

    def install(self):
        if not self.isInstalled():
            raise NotImplementedError()


class CuisineBaseLoader:

    def __init__(self, executor, cuisine):
        self.executor = executor
        self.cuisine = cuisine
        myClassName = str(self.__class__).split(".")[-1].split("'")[0]
        localdir = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
        classes = [j.sal.fs.getBaseName(item)[7:-3] for item in j.sal.fs.listFilesInDir(localdir, filter="Cuisine*")]
        for className in classes:
            # import the class
            exec("from JumpScale.tools.cuisine.%s.Cuisine%s import *" % (myClassName, className))
            # attach the class to this class
            do = "self.%s=Cuisine%s(self.executor,self.cuisine)" % (className.lower(), className)
            # self.logger.info(do)
            exec(do)


class JSCuisineFactory:

    _lock = threading.Lock()
    cuisines_instance = {}
    _local = None

    def __init__(self):
        self.__jslocation__ = "j.tools.cuisine"
        self.logger = j.logger.get("j.tools.cuisine")

    def _getBaseClass(self):
        return CuisineBase

    def _getBaseAppClass(self):
        return CuisineApp

    def _getBaseClassLoader(self):
        return CuisineBaseLoader

    def reset(self, cuisine):
        """
        reset remove the cuisine instance passed in argument from the cache.
        """
        with self._lock:
            if cuisine.executor.id in self.cuisines_instance:
                del self.cuisines_instance[cuisine.executor.id]

    def resetAll(self):
        """
        reset cache of cuisine isntances
        """
        self.cuisines_instance = {}

    @property
    def local(self):
        with self._lock:
            if self._local is None:
                from JumpScale.tools.cuisine.JSCuisine import JSCuisine
                self._local = JSCuisine(j.tools.executorLocal)
            return self._local

    def _generate_pubkey(self):
        if not j.do.SSHAgentAvailable():
            j.do._loadSSHAgent()
        rc, out, err = j.sal.process.execute("ssh-add -l")
        keys = []
        for line in out.split("\n"):
            try:
                # TODO: ugly needs to be done better
                item = line.split(" ", 2)[2]
                keyname = item.split("(", 1)[0].strip()
                keys.append(keyname)
            except BaseException:
                pass
        key = j.tools.console.askChoice(keys, "please select key")
        # key = j.sal.fs.getBaseName(key)
        return j.sal.fs.fileGetContents(key + ".pub")

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
        cuisine=j.tools.cuisine.get(executor)

        executor can also be a string like: 192.168.5.5:9022

        or if used without executor then will be the local one
        """
        from JumpScale.tools.cuisine.JSCuisine import JSCuisine
        executor = j.tools.executor.get(executor)

        with self._lock:
            if usecache and executor.id in self.cuisines_instance:
                return self.cuisines_instance[executor.id]

            cuisine = JSCuisine(executor)
            self.cuisines_instance[executor.id] = cuisine
            return self.cuisines_instance[executor.id]

    def getFromId(self, id):
        executor = j.tools.executor.get(id)
        return self.get(executor)

    def test(self, executor=None):
        """
        executor can be a real executor or a hostname e.g. ovh4:22
        """
        if j.data.types.string.check(executor):
            c = j.tools.cuisine.get("ovh4")
            e = c.executor
            assert e.cuisine == c
        elif executor is None:
            e = j.tools.executorLocal

        c = e.cuisine.apps.alba
        c2 = e.cuisine.apps.ipfs

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

        assert {'CuisineAlba': {'test': 1, 'test2': {'a': 'bb'}}, 'CuisineIPFS': {'test': 1}} == e.config

        # remove all cache
        e.cacheReset()
        assert e._config is None
        assert {'CuisineAlba': {'test': 1, 'test2': {'a': 'bb'}}, 'CuisineIPFS': {'test': 1}} == e.config

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

        assert {'CuisineAlba': {'done': {'test': True}}} == e.config

        # if this takes long & writes long then not ok, need to measure time
        self.logger.info("perf test")
        for i in range(100):
            c.doneGet("test")

        e.reset()
