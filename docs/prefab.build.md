# prefab.runtimes.build

The `prefab.build` module is for building packages from source.

Methods inside `build`:

- **build**: clones a repo, builds and installs depending on the passed arguments.

Example:

```python
repo = 'https://github.com/rtsisyk/msgpuck.git'
build = j.tools.prefab.local.runtimes.build
build.build('msgpuck', repo, cmake=True, make=True, make_install=True)
```

This will clone the repo in /tmp/msgpuck, then run `cmake .`, `make` and `make install`.
