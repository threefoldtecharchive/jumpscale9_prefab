# Cuisine

The JumpScale implementation of Cuisine is a fork of the original Cuisine as available on GitHub: <https://github.com/sebastien/prefab>

Cuisine provides [Chef](https://en.wikipedia.org/wiki/Chef_(software) software-like functionality for [Fabric](http://www.fabfile.org/).

Cuisine makes it easy to automate server installations and create configuration recipes by wrapping common administrative tasks, such as installing packages and creating users and groups, in Python functions.

Cuisine takes an `executor` object as an argument, through which you connect locally or remotely.

## Local

```python
executor = j.tools.executorLocal
prefab = j.tools.prefab.get(executor)
# or simply j.tools.prefab.local
```

## Remote

```python
executor = j.tools.executor.getSSHBased(addr, port, login, passwd)
prefab = j.tools.prefab.get(executor)
```

## Cuisine modules
- [prefab.apps](prefab.apps.md)
- [prefab.bash](prefab.bash.md)
- [prefab.btrfs](prefab.btrfs.md)
- [prefab.core](prefab.core.md)
- [prefab.development](prefab.development.md)
- [prefab.group](prefab.group.md)
- [prefab.kwm](prefab.kvm.md)
- [prefab.net](prefab.net.md)
- [prefab.package](prefab.package.md)
- [prefab.processmanager](prefab.processmanager.md)
- [prefab.ssh](prefab.ssh.md)
- [prefab.systemservices](prefab.systemservices.md)
- [prefab.tmux](prefab.tmux.md)
