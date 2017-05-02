# prefab.package

The `prefab.package` module is for dealing with package managers.

Examples of methods inside `package`:

- **clean**: cleans the packaging system, e.g. remove outdated packages & caching packages
- **ensure**: ensures a package is installed
- **install**: installs a package
- **mdupdate**: updates metadata of system
- **multiInstall**: installs packages passsed as package list which is a text file and each line is a name of the package
- **remove**: removes a package
- **start**: starts the service of the package
- **update**: updates a certain package
- **upgrade**: upgrades system, passing distupgrade=True will make a distribution upgrade

```
!!!
title = "Cuisine.package"
date = "2017-04-08"
tags = []
```
