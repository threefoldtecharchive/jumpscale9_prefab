# prefab.network.zeroboot

The `prefab.network.zeroboot` module should be used to bootstrap a router with zerotier configurations

## prerequisites

* installed openwrt on a router
    - Download an OpenWrt image from https://openwrt.org/toh/views/toh_fwdownload depending on your router model.
    - Connect to the router by a LAN cable and go to http://192.168.1.1
    - Go to Router Settings > Configuration > Manual file and choose the OpenWrt image. IT will take around 5 mins to load OpenWrt, then It will restart the router.
    - Connect to the router through http://192.168.1.1, and you should see OpenWrt login page.
    - Use the default login username `admin` and keep password field empty.
    - Now, set a new password.
    - Turn `wifi` interface ON from `Network` > `Interfaces
* [**prefab prerequisites**](intro.md#prerequisites)
* [**ZeroTier**](https://www.zerotier.com/) Network ID and Token

## install

```python
sshclient = j.clients.ssh.get(instance='<instance_name>')
prefab = sshclient.prefab 
prefab.network.zeroboot.install('<zerotier_network_id>', '<zerotier_token>')
```