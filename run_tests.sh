#!/bin/bash
set -e
set -x
export SSHKEYNAME=id_rsa

# Start container
sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; ZDockerActive -b jumpscale/js9_full -i js9_full"

# Run tests
sudo -HE bash -c "ssh -tA  root@localhost -p 2222 \"cd /opt/code/github/jumpscale/prefab9; python3 ./testscripts/test_prefabs.py\""
