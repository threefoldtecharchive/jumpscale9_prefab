# intro to prefab

## prerequisites

to be able to use `prefab` you will need to have these packages installed on the remote machine:  
* bash
* openssh-sftp-server
* openssl-util
* coreutils-base64
* tmux  

you can install these packages manually or you can just run this snippet (after configuring a sshclient)

```python
sshclient.execute(cmd="opkg update") sshclient.execute(cmd="opkg install bash") sshclient.execute(cmd="opkg install openssh-sftp-server")
sshclient.execute(cmd="opkg install openssl-util") sshclient.execute(cmd="opkg install coreutils-base64")
sshclient.execute(cmd="opkg install tmux") 
```
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
