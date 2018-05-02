# prefab.network.zeroboot

The `prefab.network.zeroboot` module should be used to bootstrap a router with zerotier configurations

## prerequisites

* Install openwrt on your router:
    - Upgrading from a previous OpenWRT (lede) version:
        - Download the correct sysupgrade image from http://lede.gig.tech/targets/mvebu/cortexa9/ depending on your router model.
        - Go to System > Backup flash firmware > Flash new firmware image > Image and choose the OpenWrt image. It will take around 5 mins to load OpenWrt, then It will restart the router. 
    - Installing OpenWRT on a brand new router:
        - Download the correct factory image from http://lede.gig.tech/targets/mvebu/cortexa9/ depending on your router model.
        - Go to Router Settings > Configuration > Manual file and choose the OpenWrt image. It will take around 5 mins to load OpenWrt, then It will restart the router.
    - Connect to the router by a LAN cable and go to http://192.168.1.1
    - Connect to the router through http://192.168.1.1, and you should see OpenWrt login page.
    - Use the default login username `admin` and keep password field empty.
    - Now, set a new password.
    - Turn `wifi` interface ON from `Network` > `Interfaces
* [**prefab prerequisites**](../README.md#Prerequisites)
* [**ZeroTier**](https://www.zerotier.com/) Network ID and Token

## install

```python
sshclient = j.clients.ssh.get(instance='<instance_name>')
# Install prefab requirements
sshclient.execute(cmd="opkg update")
sshclient.execute(cmd="opkg install bash openssh-sftp-server openssl-util coreutils-base64 tmux")
# Use the zeroboot prefab to configure the router
prefab = sshclient.prefab 
prefab.network.zeroboot.install('<zerotier_network_id>', '<zerotier_token>')
```