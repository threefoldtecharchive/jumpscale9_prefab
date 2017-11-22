#!/bin/bash
set -e
set -x

export SSHKEYNAME=id_rsa

if [ -n $TRAVIS_EVENT_TYPE ] && [ $TRAVIS_EVENT_TYPE == "cron" ]; then
    # Start js9 container
    sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; ZDockerActive -b jumpscale/js9_full -i js9_full"
else
    # Start ays9 container
    sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; ZDockerActive -b jumpscale/ays9nightly -i ays9"
    sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; container 'pip install -e /opt/code/github/jumpscale/core9'"
    sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; container 'pip install -e /opt/code/github/jumpscale/lib9'"
    sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; container 'pip install -e /opt/code/github/jumpscale/prefab9'"
fi

# Run tests
sudo -HE bash -c "ssh -tA  root@localhost -p 2222 \"cd /opt/code/github/jumpscale/prefab9; python3 ./testscripts/test_prefabs.py\""
