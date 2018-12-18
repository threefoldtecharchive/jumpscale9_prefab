from Jumpscale import j
import inspect

JSBASE = j.application.JSBaseClass
class PrefabBase(JSBASE):

    def __init__(self, executor, prefab):
        JSBASE.__init__(self,init=False)
        self._classname = ""
        self.executor = executor
        self.prefab = prefab
        if "core" in prefab.__dict__:
            self.core = self.prefab.core
        else:
            print("NO CORE IN PREFAB")
        self._initenvDone = False
        self.env = self.executor.env

        if self.classname != 'PrefabCore':
            self.core = prefab.core

        self._init()


    def _init(self):
        pass #NEEDS TO REMAIN EMPTY BECAUSE IS USED AT HIGHER LEVEL LAYER


    def replace(self, txt, args=None):
        if args is None:
            args={}
        return self.executor.replace(txt,args=args)


    def reset(self):
        self.doneReset()
        self._init()

    @property
    def done(self):
        j.shell()
        w


    def doneReset(self):
        """
        resets the remembered items which are done
        """
        self.executor.state_deleteall()


    def doneSet(self, key):
        if self.executor.readonly:
            self._logger.debug("info: Canot do doneset:%s because readonly" % key)
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
            self.executor.state_set(item)

        return True

    def doneDelete(self, key):
        if self.executor.readonly:
            self._logger.debug("info: Canot do doneDelete:%s because readonly" % key)
            return False
        if key.find(",") != -1:
            key = [item.strip() for item in key.split(",")]
        elif key.find("\n") != -1:
            key = [item.strip() for item in key.split("\n")]
        elif not j.data.types.list.check(key):
            key = [key]
        for item in key:
            if item.strip() == "":
                continue
            self.executor.state_delete(item)

    def doneGet(self, key):
        if self.executor.readonly:
            return False
        return self.executor.state_exists(key)

    # def doneCheck(self, cat, reset=False):
    #     """
    #     specify category to test against
    #     if $CLASS.NAME specified then will call the isInstalled method which checks if command is installed
    #
    #     will call doneGet and take reset into account
    #
    #     reset can be 1, "1", True, ...
    #
    #     if done will return : True
    #     """
    #     reset = j.data.serializers.fixType(reset, False)
    #     if reset is False and self.doneGet(cat):
    #         return True
    #     return False

    @property
    def classname(self):
        if self._classname == "":
            self._classname = str(self.__class__).split(".")[-1].strip("'>")
        return self._classname

    @property
    def id(self):
        return self.executor.id

    @property
    def cache(self):
        if self._cache is None:
            self._cache = j.core.cache.get("prefab" + self.id + self.classname, reset=True, expiration=600)  # 10 min
        return self._cache


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
    #     reset = j.data.serializers.fixType(reset, False)
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
        classes = [j.sal.fs.getBaseName(item)[6:-3] for item in j.sal.fs.listFilesInDir(localdir, filter="Prefab*")]
        for className in classes:
            # import the class
            exec("from JumpscalePrefab.%s.Prefab%s import *" %
                 (myClassName, className))
            # attach the class to this class
            do = "self.%s=Prefab%s(self.executor,self.prefab)" % (
                className.lower(), className)
            # self._logger.info(do)
            exec(do)
