from Jumpscale import j
import inspect

JSBASE = j.application.JSBaseClass
class PrefabBase(JSBASE):

    def __init__(self, executor, prefab):
        JSBASE.__init__(self)
        self._classname = ""
        self.executor = executor
        self.state = executor.state
        self.config = self.state.config
        self.prefab = prefab
        self._initenvDone = False
        self._logger = None
        self.env = self.executor.env

        if self.classname != 'PrefabCore':
            self.core = prefab.core

        self._init()

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get(self.classname)
        return self._logger

    def _init(self):
        pass #NEEDS TO REMAIN EMPTY BECAUSE IS USED AT HIGHER LEVEL LAYER


    def replace(self, txt, args={}):
        txt = j.core.text.strip(txt)
        for item in self.__dict__.keys():
            if item == item.upper():
                txt = txt.replace("$%s" % item, self.__dict__[item])
        txt = self.core.replace(txt, args=args)
        return txt



    def reset(self):
        self.executor.state.stateSet(self.classname, {})
        self.doneReset()
        self._init()

    @property
    def done(self):
        return self.state.stateGet(self.classname,{},True)

    def doneReset(self):
        """
        resets the remembered items which are done
        """
        self.state.stateSet(self.classname,{},save=True)


    def doneSet(self, key):
        if self.executor.readonly:
            self.logger.debug("info: Canot do doneset:%s because readonly" % key)
            return False
        done = self.done
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
            done[item] = True
        self.state.stateSet(self.classname,done,save=True)
        return True

    def doneDelete(self, key):
        if self.executor.readonly:
            self.logger.debug("info: Canot do doneDelete:%s because readonly" % key)
            return False
        done = self.done
        if key in done:
            del (done[key])
        self.state.stateSet(self.classname,done,save=True)
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
        reset = j.data.serializers.fixType(reset, False)
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
            # self.logger.info(do)
            exec(do)
