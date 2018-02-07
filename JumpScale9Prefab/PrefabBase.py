from js9 import j
import inspect

JSBASE = j.application.jsbase_get_class()
class PrefabBase(JSBASE):

    def __init__(self, executor, prefab):
        JSBASE.__init__(self)
        self._classname = ""
        self.executor = executor
        self.executor.dir_paths
        self.prefab = prefab
        self._initenvDone = False
        self.env = self.executor.env

        if self.classname != 'PrefabCore':
            self.core = prefab.core
        self._init()

    def _init(self):
        pass

    def replace(self, txt, args={}):
        txt = j.data.text.strip(txt)
        for item in self.__dict__.keys():
            if item == item.upper():
                txt = txt.replace("$%s" % item, self.__dict__[item])
        txt = self.core.replace(txt, args=args)
        return txt

    @property
    def config(self):
        """
        """
        return self.executor.state.stateGet(self.classname, {}, set=True)

    def configSave(self):
        self.executor.state.stateSet(self.classname, self.config)

    def cacheReset(self):
        self.executor.cache.reset()
        j.data.cache.reset(self.id)

    def reset(self):
        self.executor.state.stateSet(self.classname, {})
        self.cacheReset()
        self._init()

    @property
    def done(self):
        if "done" not in self.config:
            self.config["done"] = {}
        return self.config["done"]

    def doneReset(self):
        """
        resets the remembered items which are done
        """
        self.reset()
        # if "done" in self.config:
        #     self.config.pop("done")
        # if not self.executor.readonly:
        #     # this will make sure it gets set remotely
        #     self.configSet("done", {})

    def doneSet(self, key):
        if self.executor.readonly:
            self.logger.debug(
                "info: Canot do doneset:%s because readonly" % key)
            return False
        # bring to list of keys
        if key.find(",") != -1:
            key = [item.strip() for item in key.split(",")]
        elif key.find("\n") != -1:
            key = [item.strip() for item in key.split("\n")]
        elif not j.data.types.list.check(key):
            key = [key]
        for item in key:
            if item.strip() == "":
                continue
            self.done[item] = True
        self.executor._config_changed = True
        self.configSave()
        return True

    def doneDelete(self, key):
        if self.executor.readonly:
            self.logger.debug(
                "info: Canot do doneDelete:%s because readonly" % key)
            return False
        self.done[key] = False
        self.executor._config_changed = True
        self.configSave()
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

    def doneCheck(self, cat, reset=False):
        """
        specify category to test against
        if $CLASS.NAME specified then will call the isInstalled method which checks if command is installed

        will call doneGet and take reset into account

        reset can be 1, "1", True, ...

        if done will return : True
        """
        reset = j.data.serializer.fixType(reset, False)
        if reset is False and self.doneGet(cat):
            return True
        return False

    @property
    def classname(self):
        if self._classname == "":
            self._classname = str(self.__class__).split(".")[-1].strip("'>")
        return self._classname

    @property
    def id(self):
        return self.executor.id

    def __str__(self):
        return "%s:%s" % (self.classname, self.executor.id)

    __repr__ = __str__


class PrefabApp(PrefabBase):

    NAME = None

    # def __init__(self, executor, prefab):
    #     super().__init__(executor=executor, prefab=prefab)

    # NOT GOING TO USE THE COMMAND CHECK, NOT REALLY NEEDED
    # def doneCheck(self, cat, reset=False):
    #     """
    #     specify category to test against
    #     if $CLASS.NAME specified then will call the isInstalled method which checks if command is installed

    #     will call doneGet and take reset into account

    #     reset can be 1, "1", True, ...

    #     if done will return : True
    #     """
    #     reset = j.data.serializer.fixType(reset, False)
    #     if reset is False and self.isInstalled() and self.doneGet(cat):
    #         return True
    #     return False

    def isInstalled(self):
        """
        Checks if a package is installed or not
        You can ovveride it to use another way for checking
        """
        return self.prefab.core.command_check(self.NAME)

    def isStarted(self):
        """
        Checks if a package already started
        You can ovveride it to use another way for checking
        """
        return not self.prefab.core.run('pgrep %s' % self.NAME, die=False)[0]

    def install(self):
        if not self.isInstalled():
            raise NotImplementedError()


class PrefabBaseLoader(JSBASE):

    def __init__(self, executor, prefab):
        JSBASE.__init__(self)
        self.executor = executor
        self.prefab = prefab
        myClassName = str(self.__class__).split(".")[-1].split("'")[0]
        localdir = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
        classes = [j.sal.fs.getBaseName(
            item)[6:-3] for item in j.sal.fs.listFilesInDir(localdir, filter="Prefab*")]
        for className in classes:
            # import the class
            exec("from JumpScale9Prefab.%s.Prefab%s import *" %
                 (myClassName, className))
            # attach the class to this class
            do = "self.%s=Prefab%s(self.executor,self.prefab)" % (
                className.lower(), className)
            # self.logger.info(do)
            exec(do)
