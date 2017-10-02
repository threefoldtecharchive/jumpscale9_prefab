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
        if self._{{name}} == None:
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

class PrefabLoader():

    def __init__(self):
        self.moduleList={}
        self.logger = j.logger.get("jsprefabloader")

    # @property
    # def initPath(self):
    #     path = j.tools.jsloader._findSitePath() + "/js9prefab.py"
    #     # print("initpath:%s" % path)
    #     j.sal.fs.remove(path)
    #     return path

    # def processLocationSub(self,jlocationSubName,jlocationSubList):
    #     #import a specific location sub (e.g. j.clients.git)

    #     def removeDirPart(path):
    #         "only keep part after jumpscale9"
    #         state = 0
    #         res = []
    #         for item in path.split("/"):
    #             if state == 0 and item.lower().find("jumpscale9") != -1:
    #                 state = 1
    #             if state == 1:
    #                 res.append(item)

    #         if res[0] == res[1] and res[0].casefold().find("jumpscale9") !=-1:
    #             res.pop(0)
    #         return "/".join(res)

    #     classfile, classname, importItems = jlocationSubList

    #     generationParamsSub = {}
    #     generationParamsSub["classname"] = classname
    #     generationParamsSub["name"] = jlocationSubName
    #     importlocation = removeDirPart(classfile)[:-3].replace("//", "/").replace("/", ".")
    #     generationParamsSub["importlocation"] = importlocation

    #     rc=0

    #     return rc,generationParamsSub


    # def generate(self):
    #     """
    #     generate's the jumpscale init file for prefab: js9prefab

    #     js9 'j.tools.prefab.loader.generate()'

    #     """
    #     path = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
    #     path=j.sal.fs.joinPaths(j.sal.fs.getParent(path),"modules")
    #     out = self.initPath
    #     print("* js9 prefab generate path:%s, localpath:%s" % (out,path))

    #     content = GEN_START

    #     jlocations = {}
    #     jlocations["locations"] = []

    #     if not j.sal.fs.exists(path, followlinks=True):
    #         raise RuntimeError("Could not find prefab dir:%s"%path)

    #     moduleList = self.findModules(path=path,moduleList=self.moduleList)

    #     for jlocationRoot, jlocationRootDict in moduleList.items():

    #         #is per item under j e.g. j.clients

    #         if not jlocationRoot.startswith("j."):
    #             raise RuntimeError()

    #         jlocations["locations"].append({"name":jlocationRoot[2:]})

    #         generationParams = {}
    #         generationParams["locationsubserror"] = []
    #         generationParams["jname"] = jlocationRoot.split(".")[1].strip()                           #only name under j e.g. tools
    #         generationParams["locationsubs"]=[]


    #         #add per sublocation to the generation params
    #         for jlocationSubName, jlocationSubList in jlocationRootDict.items():

    #             rc,generationParamsSub=self.processLocationSub(jlocationSubName,jlocationSubList)

    #             if rc==0:
    #                 #need to add
    #                 generationParams["locationsubs"].append(generationParamsSub)

    #         #put the content in
    #         content0CC = pystache.render(GEN2, **generationParams)
    #         content0 = pystache.render(GEN, **generationParams)
    #         if len([item for item in content0CC.split("\n") if item.strip() != ""]) > 4:
    #             contentCC += content0CC
    #         if len([item for item in content0.split("\n") if item.strip() != ""]) > 4:
    #             content += content0

    #     contentCC += pystache.render(GEN_END2, **jlocations)
    #     content += pystache.render(GEN_END, **jlocations)


    #     j.sal.fs.writeFile(outCC, contentCC)

    #     j.sal.fs.writeFile(out, content)

    def load(self, executor, prefab, moduleList=None):
        """
        walk over code files & find locations for jumpscale modules

        return as dict

        format

        [$rootlocationname][$locsubname]=(classfile,classname,importItems)

        """

        path = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
        path=j.sal.fs.joinPaths(j.sal.fs.getParent(path), "modules")

        if moduleList is None:
            moduleList = self.moduleList

        self.logger.info("find prefab modules in %s" % path)

        for cat in j.sal.fs.listDirsInDir(path, recursive=False, dirNameOnly=True, findDirectorySymlinks=True, followSymlinks=True):
            catpath=j.sal.fs.joinPaths(path, cat)
            # print(1)
            # print("prefab.%s = PrefabCat()"%cat)
            exec("prefab.%s = PrefabCat()" % cat)

            if catpath not in sys.path:
                sys.path.append(catpath)

            if not j.sal.fs.exists("%s/__init__.py" % catpath):
                j.sal.fs.writeFile("%s/__init__.py" % catpath,"")

            # print ("CATPATH:%s"%catpath)

            for classfile in j.sal.fs.listFilesInDir(catpath, False, "*.py"):
                # print(classfile)
                basename = j.do.getBaseName(classfile)
                basename = basename[:-3]

                # print ("load prefab module:%s"%classfile)

                if not basename.startswith("Prefab"):
                    continue

                exec("from %s import %s" % (basename, basename))
                prefabObject = eval("%s(executor,prefab)" % basename)

                basenameLower = basename.replace("Prefab", "")
                basenameLower = basenameLower.lower()

                exec("prefab.%s.%s = prefabObject" % (cat,basenameLower))

        #         from IPython import embed;embed(colors='Linux')
        #         j

        #         for classname, item in self.findJumpscaleLocationsInFile(classfile).items():
        #             #item has "import" & "location" as key in the dict
        #             if "location" in item:
        #                 location = item["location"]
        #                 if "import" in item:
        #                     importItems = item["import"]
        #                 else:
        #                     importItems = []

        #                 locRoot = ".".join(location.split(".")[:-1])
        #                 locSubName = location.split(".")[-1]
        #                 if locRoot not in moduleList:
        #                     moduleList[locRoot] = {}
        #                 moduleList[locRoot][locSubName]=(classfile,classname,importItems)
        # return moduleList
