# prefab.kubernetes

The `prefab.virtualization.kubernetes` module is responsible for deploying a kubernetes cluster and configuring the networking between using the flannel module.

available methods include but are not limited to:

 - This will install the kubelet kubeadm and kubectl modules on a single machine. To allow running a cluster using kubelet and kubeadm and controlling them using kubectl.

```python
c = j.tools.prefab.local
c.virtualization.install_base()
```
 - Another more abstract method is used to deploy the entire cluster installing both master and minions (or masters as minions using the unsafe flag) and setting up flannel.
 P.s Make sure to clean your known hosts from any conflicting identities
```
c = j.tools.prefab.local
c1 = j.tools.prefab.get('<machineip1>')
c2 = j.tools.prefab.get('<machineip2>')
config, join_line = c.virtualization.multihost_install([c1, c2])
```

 - It is also easy to add another minion node using the join_line returned from the multihost_install using another method the install minion.
 ```
 c3 = j.tools.prefab.get('<machineip3>')
 c3.virtualization.install_minion(join_line)
 ```

```
!!!
title = "Prefab.kubernetes"
date = "2017-04-08"
tags = []
```
