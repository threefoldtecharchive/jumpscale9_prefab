# KVM

You can Access it as follows:

```python
prefab.systemservices.kvm
```

It's a prefab module that wraps the sal.kvm module for remote kvm handling.

## Example

```python

c = j.tools.prefab.local

# install kvm
c.systemservices.kvm.install()

# install OpenVswitch
c.systemservices.openvswitch.install()

# create bridge vms1
c.systemservices.openvswitch.networkCreate("vms1")
# configure the network and the natting
c.net.netconfig('vms1', '10.0.4.1', 24, masquerading=True, dhcp=True)
c.processmanager.start('systemd-networkd')
# add a dhcp sercer to the bridge
c.apps.dnsmasq.config('vms1')
c.apps.dnsmasq.install()

# create a pool for the images and virtual disks
c.systemservices.kvm.poolCreate("vms")

# get xenial server cloud image
c.systemservices.kvm.download_image("https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-uefi1.img")

# create a virutal machine kvm1 with the default settings
kvm1 = c.systemservices.kvm.machineCreate("kvm1")
# create a virutal machine kvm2 with the default settings
kvm2 = c.systemservices.kvm.machineCreate("kvm2")

# enable sudo mode
kvm1.prefab.core.sudomode=True
kvm2.prefab.core.sudomode=True

```

```
!!!
title = "Prefab.kvm"
date = "2017-04-08"
tags = []
```
