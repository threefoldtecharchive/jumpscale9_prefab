#!/bin/bash
set -e
set -x

export SSHKEYNAME=id_rsa

# Start js9 container
sudo -HE bash -c "source /opt/code/github/threefoldtech/jumpscale_bash/zlibs.sh; ZKeysLoad; ZDockerActive -b jumpscale/js9_full -i js9_full"
