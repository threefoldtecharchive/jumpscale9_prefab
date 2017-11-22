#!/bin/bash
set -e
set -x

sudo -HE bash -c "ssh-keygen -t rsa -N \"\" -f /root/.ssh/id_rsa"
export SSHKEYNAME=id_rsa

# Start container
sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; ZDockerActive -b jumpscale/ays9nightly -i ays9"
sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; container 'pip install -e /opt/code/github/jumpscale/core9'"
sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; container 'pip install -e /opt/code/github/jumpscale/lib9'"
sudo -HE bash -c "source /opt/code/github/jumpscale/bash/zlibs.sh; ZKeysLoad; container 'pip install -e /opt/code/github/jumpscale/prefab9'"

# Dump the environment variables as json file in a the container cfg dir
sudo -HE bash -c "python -c 'import json, os;print(json.dumps({\"BACKEND_ENV\": dict([(key, value) for key, value in os.environ.items() if key.startswith(\"BACKEND_\")])}))' > ~/js9host/cfg/ays_testrunner.json"

# Run tests
sudo -HE bash -c "ssh -tA  root@localhost -p 2222 \"cd /opt/code/github/jumpscale/prefab9; python ./testscripts/test_prefabs.py\""
