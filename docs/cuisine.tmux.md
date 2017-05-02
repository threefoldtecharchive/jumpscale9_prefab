# prefab.tmux

The `prefab.tmux` module is a client for tmux.

Examples of methods inside tmux:

- **attachSession**: attach to a running session
- **configure**: write the default tmux configuration
- **createSession**: create a new tmux session
- **createWindow**: create a window in a session
- **executeInScreen**: execute a command
- **getSessions**: list the running sessions
- **getWindows**: list the running windows in a session
- **killSession**: kill a session
- **killSessions**: kill all sessions
- **killWindow**: kill a window
- **logWindow**: store the stdout of a window in a file
- _*windowExists_: check if a window exist

Example:

```python
tmux = j.tools.prefab.local.tmux
tmux.createSession('s1', ['w1', 'w2'])
tmux.executeInScreen('s1', 'w1', 'ping 8.8.8.8')
tmux.executeInScreen('s1', 'w2', 'python3 -m http.server')
tmux.killSession('s1')
```

```
!!!
title = "Cuisine.tmux"
date = "2017-04-08"
tags = []
```
