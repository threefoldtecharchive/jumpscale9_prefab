# intro to prefab

## on each class the following primitives are available

```python3
#get local prefab instance
p=j.tools.prefab.local

```

### replace()

```python
def replace(self, text, args={}):
    """
    replace following args (when jumpscale installed it will take the args from there)

    uses http://mustache.github.io/ syntax
    {{varname}}


    dirs:
    - BASEDIR
    - JSAPPSDIR
    - TEMPLATEDIR
    - VARDIR
    - GOPATH
    - GOROOT
    - BINDIR
    - CODEDIR
    - JSCFGDIR
    - HOMEDIR
    - JSLIBDIR
    - LIBDIR
    - LOGDIR
    - PIDDIR
    - TMPDIR
    system
    - HOSTNAME

    args are additional arguments in dict form
```

example how to use in your prefab class (example is in caddy)

```python
C = """
:{{PORT}}
gzip
log {{LOGDIR}}/access.log
root {{WWWROOTDIR}}
"""

args = {}
args["WWWROOTDIR"] = wwwrootdir
args["LOGDIR"] = logdir
args["PORT"] = str(port)
args["EMAIL"] = email

C = self.replace(C, args)
```
