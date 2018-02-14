## Prefab Modules
This is the package hosting all the components of prefab

## Steps of creating prefab module
1- Find a suitable subpackage to put your module in.
   apps, db, ...
   
2- Create a class for you component, make it inherit from PrefabApp
You can get PrefabApp like this

```
from js9 import j
app = j.tools.prefab._getBaseAppClass()

class PrefabModule(app):
  #rest of the code
```

3- add your implementation of the following functions
 - build  
 - install
 - start
 - stop
   
   
4- You should override any function when you want to add some custom logic to it

5- run ```js9_init``` to load the new module to jumpscale

6- to test 
 - Open jumpscale shell 
 - get prefab instance
 - access your module under the package containing it

This example of how to access redis module in prefab 
```
# js9
[Wed14 15:13] - Application.py      :109 :j.application                  - INFO     - ***Application started***: jsshell
^[[APython 3.5.2 (default, Sep 14 2017, 22:51:06) 
Type 'copyright', 'credits' or 'license' for more information
IPython 6.1.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: prefab = j.tools.prefab.local

In [2]: prefab.db.redis  
```
