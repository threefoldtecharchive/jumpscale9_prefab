# How to add new module to prefab
1- Find a suitable subpackage to put your module in.
   apps, db, ...
   
2- Create a class for you component, make it inherit from PrefabApp
You can get PrefabApp like this

```python
from js9 import j
base = j.tools.prefab._getBaseClass()

class PrefabModule(base):
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
```python
# js9
In [1]: prefab = j.tools.prefab.local

In [2]: prefab.db.redis  
```
