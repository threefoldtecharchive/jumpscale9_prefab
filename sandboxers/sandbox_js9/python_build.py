from js9 import j


from lib.base import *



builder_machine, _ = node_get("pythonbuilder")

builder_prefab = builder_machine.prefab
builder_prefab.system.package.install('rsync')
builder_prefab.core.run("js9 'j.tools.sandboxer.python.do()'")


tester_machine, _ = node_get("tester",base=False, reset=True)#get empty machine

tester_prefab = tester_machine.prefab
tester_prefab.system.package.install('rsync')
ipaddr = builder_machine.ipaddr_priv


pub_ssh_key_path = tester_prefab.system.ssh.keygen()
sshkey = tester_prefab.core.file_read(pub_ssh_key_path)
builder_prefab.system.ssh.authorize('root', sshkey)


cmd = "eval `ssh-agent -s`; ssh-add %s;mkdir /tmp/js9_sb;rsync -avzr -e \"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null\" %s:/opt/var/build/sandbox/python3/ /tmp/js9_sb/" % (pub_ssh_key_path[:-4], ipaddr)
print(cmd)
tester_prefab.core.run(cmd)
cmd = "cd /tmp/js9_sb;source env.sh;js9 'print(\"WORKS\")'"
print(cmd)
tester_prefab.core.run(cmd)

