# Introduction
This document describes the details of an atomicswap test environment setup. the main goals of the the document are:
- Architecture of test environment
- How to setup your test environment
- Explains the details of atomicswap process

## Test environment architecture
The following diagram shows the main components of the atomicswap setup
![Atomicswap setup](https://raw.githubusercontent.com/Jumpscale/sandbox/master/crypto_sandboxing/atomicswap_setup.jpg)

The setup shows:
- One zero-os node running on packet.net
- A node robot container running on top of the ZOS node
- Two VMs created via the node robot each one is running a full node on BTC and TFT networks recpectivly
- A js9 node where the atomicswap SAL can be executed

## How to setup your test environment
We provide an end2end script that can be used to do a complete setup of the environment. The script needs to run from a JS9 node and it needs the following clients to be configured:
- At least one sshkey client to be configured and loaded
- At least one zerotier client to be configured
- At least one packet client to be configured

### Environment Variables
The setup depends on some variables that would be used to control how the setup will be deployed and also configur the single VMs running the bockchains. The following environment variables can be set before running the deploy script to set the different values of the variables
- ZT_NET_ID: [REQUIRED] This is the only required environment variables to be set, if it is not set then the script will fail since we will not know which zerotier netowrk to use when setting up the zero-os node. Make sure that your API token that is configured in the zerotier client have access to this network.
- SSHKEY_NAME: [default: id_rsa] This will be the keyname of the sshkey to be used to authorized the current node to communicate with the remote nodes created during the deployment.
- ZT_CLIENT_INSTANCE: [default: main] Name of the zerotier client instance to be used.
- PACKET_CLIENT_INSTANCE: [default: main] Name of the packet.net client instance to be used.
- TFT_WALLET_PASSPHRASE: [default: pass] Passphrase for initializing the TFT wallet.
- TFT_WALLET_RECOVERY_SEED: [default: None] Recovery seed of TFT wallet, if not provided, new wallet will be initialized.
- ZOS_NODE_NAME: [default: atomicswap.test] Name of the Zero-OS node to be created on top of Packet.net

### Starting the deploy script
If you already have the the pre-requisites satisfied and at least exported the ZT_NET_ID variable then you are ready to run the deploy script.To do that you need to execute the following command on the js9 node where you configured your clients:
```bash
export ZT_NET_ID=<network_id>
js9 'j.clients.git.pullGitRepo("https://github.com/Jumpscale/sandbox.git")'
python3 /opt/code/github/threefoldtech/sandbox/crypto_sandboxing/deploy.py
```
The script will do the following steps:
- Create a ZOS node on packet.net with the name of ZOS_NODE_NAME variable
- Create two VMs each containing the bockchains binaries using the flist [https://hub.gig.tech/abdelrahman_hussein_1/ubuntucryptoexchange.flist]
- Forward port 2250 to connect to the TFT node.
- Forward port 2350 to connect to the BTC node.
- Start blockchains on the two VMS
- On the TFT node, it will initialize the wallet using the provided passphrase and recovery seed or use the default values
- Wait for the blockchains to sync with the respective networks.

### Adding funds to the wallets
By now you should have two full nodes, one BTC node and another TFT Node. To be able to make an atomicswap enough funds need to exist in both wallets.
If you already configured the TFT_WALLET_RECOVERY_SEED and that seed already have funds then you dont need to do anything for the TFT Node. If you do not have funds on that seed or you did not provide recovery seed, then you need to transfer funds to your wallet.
#### Adding funds to the TFT node wallet
First you need to get an address from the TFT wallet, you can do that by executing the following commands on the js9 node that ran the deploy script
```python
tft_prefab = j.tools.prefab.getFromSSH(<zt_ip_address_of_zos_node>, port=2250)
tft_prefab.core.run('tfchainc wallet address')[1]
* RUN:tfchainc wallet address
Out[8]: 'Created new address: 010b5b9c062731dad10f87f67722ea37e578c4808a14f6b251b4fc106f25ea6568031d8be296f4'
```
You then need to contact the rivine team to send you funds on this address.

#### Adding funds to the BTC node wallet
First you need to get an address from the BTC wallet, you cn do that by executing the following commands on the js9 noce that ran the deploy script
```python
btc_prefab = j.tools.prefab.getFromSSH(<zt_ip_address_of_zos_node>, port=2350)
 btc_prefab.core.run('bitcoin-cli getnewaddress ""')[1]
* RUN:bitcoin-cli getnewaddress ""
* EXECUTE localhost:2222: [ ! -e '/root/.bash_profile' ] && touch '/root/.bash_profile' ;source /root/.bash_profile;bitcoin-cli getnewaddress ""
INFO:pssh.host_logger:[localhost]       2MwekrLGQFqpTTEWtmWzn3R25B7Ft8DBX9g
* 2MwekrLGQFqpTTEWtmWzn3R25B7Ft8DBX9g
Out[11]: '2MwekrLGQFqpTTEWtmWzn3R25B7Ft8DBX9g'
```
Then you can use the above address to transfer funds to it. You can do that by visiting the following website [https://testnet.manu.backend.hamburg/faucet]

Once you have funds in both wallets then you can start using the atomicswap tool


## Atomicswap process
Atomicswap is a method that allows two users from two different chains to exchange funds after agreeing of the amount from each cryptocurrency.
A more detailed description and example of the atomicswap process can be found here: [https://github.com/rivine/rivine/blob/master/doc/atomicswap/atomicswap.md#theory]
We support atomicswap between TFT and BTC and we provide a JS9 SAL that make it very easy to to automate the atomicswap process.
You can check how to use the atomicswap SAL using the documentation here: [https://github.com/Jumpscale/lib9/tree/atomicswap/Jumpscale9Lib/tools/atomicswap]


# Creating a Jumpscale Decentralized Exchange(DEX) flist
A Jumpscale DEX is a flist that contains all the services needed to run a container/node that can be part of a Decentralized network for exchanging cryptocurrencies.
The flist [js9_dex](https://hub.gig.tech/abdelrahman_hussein_1/js9_dex.flist) is based on an [ubuntu image](https://hub.gig.tech/gig-official-apps/ubuntu1604-for-js.flist) and it is merged with:
- Boot files for ubunto xenial [flist](https://hub.gig.tech/abdelrahman_hussein_1/ubuntu_xenial_boot.flist)
- Jumpscale [flist](https://hub.gig.tech/abdelrahman_hussein_1/js9_sandbox.flist)
- Electrum [flista](https://hub.gig.tech/abdelrahman_hussein_1/electrum.flist)

To create the flist, you need to execute the following command:
```python
python3 /opt/code/github/threefoldtech/sandbox/crypto_sandboxing/cryptosandbox_local.py
```

If everything goes well, then you will find a copy of the js9_dex.flist and electrum.flist in the account configured via the existing IYO account.
