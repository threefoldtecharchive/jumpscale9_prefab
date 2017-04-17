# Cuisine

The JumpScale implementation of Cuisine is a fork of the original Cuisine as available on GitHub: <https://github.com/sebastien/cuisine>

Cuisine provides [Chef](https://en.wikipedia.org/wiki/Chef_(software) software-like functionality for [Fabric](http://www.fabfile.org/).

Cuisine makes it easy to automate server installations and create configuration recipes by wrapping common administrative tasks, such as installing packages and creating users and groups, in Python functions.

Cuisine takes an `executor` object as an argument, through which you connect locally or remotely.

## Local

```python
executor = j.tools.executorLocal
cuisine = j.tools.cuisine.get(executor)
# or simply j.tools.cuisine.local
```

## Remote

```python
executor = j.tools.executor.getSSHBased(addr, port, login, passwd)
cuisine = j.tools.cuisine.get(executor)
```

## Cuisine modules
- [cuisine.apps](cuisine.apps.md)
- [cuisine.bash](cuisine.bash.md)
- [cuisine.btrfs](cuisine.btrfs.md)
- [cuisine.core](cuisine.core.md)
- [cuisine.development](cuisine.development.md)
- [cuisine.group](cuisine.group.md)
- [cuisine.kwm](cuisine.kvm.md)
- [cuisine.net](cuisine.net.md)
- [cuisine.package](cuisine.package.md)
- [cuisine.processmanager](cuisine.processmanager.md)
- [cuisine.ssh](cuisine.ssh.md)
- [cuisine.systemservices](cuisine.systemservices.md)
- [cuisine.tmux](cuisine.tmux.md)
