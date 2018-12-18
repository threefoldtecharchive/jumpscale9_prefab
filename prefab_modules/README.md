# How to add a new module to prefab
1- Find a suitable subpackage to put your module in.
   apps, db, ...
   
2- Create a class for your component, let it inherit from PrefabApp

```python
from Jumpscale import j
base = j.tools.prefab._BaseClass

class PrefabModule(base):
  #rest of the code
```

3- add your implementation of the following functions
 - build  
 - install
 - start
 - stop
   
   
4- You should override any function when you want to add some custom logic to it

5- run ```js_init``` to load the new module to jumpscale

6- to test 
 - Open jumpscale shell 
 - get prefab instance
 - access your module under the package containing it

This example of how to access redis module in prefab 
```python
# jumpscale
In [1]: prefab = j.tools.prefab.local

In [2]: prefab.db.redis  
```
