# prefab.network.zeroboot

The `prefab.network.zeroboot` module should be used to bootstrap a router with zerotier configurations

## prerequisites

* installed openwrt on a router (with ssh access)
* [**prefab prerequisites**](intro.md#prerequisites)
* [**ZeroTier**](https://www.zerotier.com/) Network ID and Token

## install

```python
sshclient = j.clients.ssh.get(instance='<instance_name>')
prefab = sshclient.prefab 
prefab.network.zeroboot.install('<zerotier_network_id>', '<zerotier_token>')
```