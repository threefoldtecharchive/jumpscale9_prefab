from JumpScale9 import j
import os
import sys
import importlib
import inspect
import json

GEN_START = """
from js9 import j
"""

GEN = """
{{#locationsubserror}}
{{classname}}=JSBase
{{/locationsubserror}}

class {{jname}}:

    def __init__(self):
        {{#locationsubs}}
        self._{{name}} = None
        {{/locationsubs}}

    {{#locationsubs}}
    @property
    def {{name}}(self):
        if self._{{name}}is None:
            # print("PROP:{{name}}")
            from {{importlocation}} import {{classname}} as {{classname}}
            self._{{name}} = {{classname}}()
        return self._{{name}}

    {{/locationsubs}}

{{#locationsubs}}
if not hasattr(j.{{jname}},"{{name}}"):
    j.{{jname}}._{{name}} = None
    j.{{jname}}.__class__.{{name}} = {{jname}}.{{name}}
{{/locationsubs}}


 """


import pystache


class PrefabCat():
    pass

JSBASE = j.application.jsbase_get_class()
class PrefabLoader(JSBASE):

    def __init__(self):
        self.moduleList = {}
        JSBASE.__init__(self)

    def load(self, executor, prefab, moduleList=None):
        """
        walk over code files & find locations for jumpscale modules

        return as dict

        format

        [$rootlocationname][$locsubname]=(classfile,classname,importItems)

        """

        path = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
        path = j.sal.fs.joinPaths(j.sal.fs.getParent(path), "modules")

        if moduleList is None:
            moduleList = self.moduleList

        self.logger.debug("find prefab modules in %s" % path)

        for cat in j.sal.fs.listDirsInDir(path, recursive=False, dirNameOnly=True, findDirectorySymlinks=True, followSymlinks=True):
            catpath = j.sal.fs.joinPaths(path, cat)
            # print(1)
            # print("prefab.%s = PrefabCat()"%cat)
            exec("prefab.%s = PrefabCat()" % cat)

            if catpath not in sys.path:
                sys.path.append(catpath)

            if not j.sal.fs.exists("%s/__init__.py" % catpath):
                j.sal.fs.writeFile("%s/__init__.py" % catpath, "")

            # print ("CATPATH:%s"%catpath)

            for classfile in j.sal.fs.listFilesInDir(catpath, False, "*.py"):
                # print(classfile)
                basename = j.sal.fs.getBaseName(classfile)
                basename = basename[:-3]

                # print("load prefab module:%s" % classfile)

                if not basename.startswith("Prefab"):
                    continue

                exec("from %s import %s" % (basename, basename))
                prefabObject = eval("%s(executor,prefab)" % basename)

                basenameLower = basename.replace("Prefab", "")
                basenameLower = basenameLower.lower()

                exec("prefab.%s.%s = prefabObject" % (cat, basenameLower))
