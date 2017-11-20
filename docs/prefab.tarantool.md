# prefab.db.tarantool

The `prefab.db.tarantool` module is for dealing with tarantool.

Examples of methods inside tarantool:

- **install**: install tarantool
- **start**: start tarantool in a tmux session
- **install_luarocks_rock**: a wrapper for `luarocks install <name>`
- **install_tarantool_rock**: a wrapper for `tarantoolctl rocks <name>`

Example:

```python
tarantool = j.tools.prefab.local.db.tarantool
tarantool.install_luarocks_rock('yaml')
tarantool.install_tarantool_rock('shard')
```
