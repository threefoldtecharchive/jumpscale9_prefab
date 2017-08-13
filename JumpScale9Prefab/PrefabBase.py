from js9 import j
import inspect



class PrefabBase:

    def __init__(self, executor, prefab):
        self._classname = ""
        self._cache = None
        self.executor = executor
        self.prefab = prefab
        self._logger = None

        if self.classname != 'PrefabCore':
            self.core = prefab.core
        self._init()

    @property
    def logger(self):
        if self._logger is None:
            self._logger = j.logger.get(self.classname)
        return self._logger

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
    def env(self,env=None):
        return self.executor.env

    @property
    def dir_paths(self):
        return self.executor.dir_paths

    def _configLocalGetFromParent(self):
        """
        is dict which is stored on node itself in msgpack format in /etc/jsexecutor.msgpack
        organized per prefab module
        """
        cfg=self.executor.config    
        from IPython import embed;embed(colors='Linux')
        if self.classname not in self.executor.config:
            self.executor.config[self.classname] = {}
        return self.executor.config[self.classname]

    def configLocalGet(self, key, defval=None):
        """
        """
        if key in self.config:
            return self.config[key]
        else:
            if defval is not None:
                self.configSet(key, defval)
                return defval
            else:
                raise j.exceptions.Input(message="could not find config key:%s in prefab:%s" %
                                         (key, self.classname), level=1, source="", tags="", msgpub="")

    def configLocalSet(self, key, val):
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

    def configLocalReset(self):
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

    @property
    def id(self):
        return self.executor.id

    @property
    def cache(self):
        if self._cache is None:
            self._cache = j.data.cache.get("prefab" + self.id + self.classname, reset=True)
        return self._cache

    def __str__(self):
        return "%s:%s" % (self.classname, self.executor.id)

    __repr__ = __str__


class PrefabApp(PrefabBase):

    NAME = None
    VERSION = None

    def __init__(self, executor, prefab):
        super().__init__(executor=executor, prefab=prefab)
        bin_dir = self.prefab.core.replace("$BINDIR")
        if bin_dir not in self.prefab.bash.profileDefault.paths:
            self.prefab.bash.profileDefault.addPath()
            self.prefab.bash.profileDefault.save()

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


class PrefabBaseLoader:

    def __init__(self, executor, prefab):
        self.executor = executor
        self.prefab = prefab
        myClassName = str(self.__class__).split(".")[-1].split("'")[0]
        localdir = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
        classes = [j.sal.fs.getBaseName(item)[6:-3] for item in j.sal.fs.listFilesInDir(localdir, filter="Prefab*")]
        for className in classes:
            # import the class
            exec("from JumpScale9Prefab.%s.Prefab%s import *" % (myClassName, className))
            # attach the class to this class
            do = "self.%s=Prefab%s(self.executor,self.prefab)" % (className.lower(), className)
            # self.logger.info(do)
            exec(do)
