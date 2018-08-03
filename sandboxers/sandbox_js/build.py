from jumpscale import j

cl=j.clients.openvcloud.get(instance="test")
space=cl.space_get()

reset=False
name="mybuild"
#if reset false, it will check if the machine exists, if yes will return

machine = space.machine_get(name, reset=reset, create=True, sshkeyname=None)

n = j.tools.nodemgr.get(name, create=False)
p = n.prefab

from IPython import embed;embed(colors='Linux')
#if sshkey is None it will use the key as used for the js9_config management tools


# j.tools.sandboxer.python.do()
# if self.core.isMac:
#     #build one on openvcloud
