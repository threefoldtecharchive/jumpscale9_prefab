# cuisine.processmanager

The `cuisine.processmanager` module is for process management.

It's used to check for a process manager on the target machine, and if it finds one it will use it; otherwise it will fall back to spawning the process in `tmux`.

You can force using a certain process manager with `cuisine.processmanager.get(name)` with `name` the name of the process manager; thi will fail in case that the process manager is not supported on the target machine.

Examples for methods in `processmanager`:

- **ensure**: for registering the process in the first time, or to ensure that it's running; For the first time you have to pass the name of the process and the command to be executed for the process and optionally the `cwd` and the environment variables; Later you can only call it using the name argument
- **start**: starts a certain process
- **stop**: stops a certain process
- **list**: list all processes
- **startAll**: starts all recognized processes

## Currently supported process managers:

### Systemd

Systemd is a process manager that uses the utility `systemctl` to start and stop services. Systemd keeps strack of a service by keeping a `.service` file under `/etc/systemd/system/`.

### RunIt

RunIt is a process manager that uses the utility `sv` to start and stop services. RunIt keeps track of services by keeping a directory with the name of the service under `/etc/service/`, the directory has an executable file 'run' that gets executed by the shell to bootstrap the service.

### Tmux

Tmux is the default process manager. The process manager module uses it in case that there is no other available process manager on the target system that is supported.

Tmux doesn't keep track of the services, and that is why the process manager module stores service information in a hash map in Redis called `processcmds`.

Starting a service is done by simply opening a window in tmux with the name of the service and starting the service in it. And stopping a service is done by closing the window with that name.

```
!!!
title = "Cuisine.processmanager"
date = "2017-04-08"
tags = []
```
