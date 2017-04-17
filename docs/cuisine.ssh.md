# cuisine.ssh

The `cuisine.ssh` module for remote SSH management.

Examples of methods inside `ssh`:

- **authorize**: ldds the given key to the '.ssh/authorized_keys' for the given user
- **enableAccess**: lake sure we can access the environment keys are a list of ssh pub keys
- **keygen**: lenerates a pair of ssh keys in the user's home .ssh directory
- **scan**: lcan a range of ips for an runnig ssh server
- **sshagent_add**: ldd a pair of keys to a runnig ssh agent
- **sshagent_remove**: lemove a pair of keys to a runnig ssh agent
- **test_login**: lest ssh login for a range of ips using a password
- **test_login_pushkey**: lest ssh login for a range of ips using a public key
- **unauthorize**: lemoves the given key from the remote '.ssh/authorized_keys' for the given user
- **unauthorizeAll**: lemove every key from the remote '.ssh/authorized_keys'

```
!!!
title = "Cuisine.ssh"
date = "2017-04-08"
tags = []
```
