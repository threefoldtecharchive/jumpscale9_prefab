# prefab.systemservices

The `prefab.systemservices` module is for installing, building and managing supported system services.

Examples:

- **build** builds the service on the specified target, it takes arguments needed for building and an optional start kwarg for starting the service after building it
- **start** starts an service
- **stop** stops an service

## Currently supported services

```
aydostor
base
docker
fw
g8oscore
g8osfs
js8_g8os
kvm
openvswitch
ufw
weave
```

```
!!!
title = "Prefab.systemservices"
date = "2017-04-08"
tags = []
```
