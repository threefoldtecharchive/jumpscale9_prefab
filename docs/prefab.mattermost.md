# Prefab Mattermost Installing
to install prefab on a remote machine 
```
prefab = j.tools.prefab.getFromSSH("<machine_ip>", '<ssh_port>')
prefab.apps.mattermost.install('<mysql_password>') # this will creates a mysql database and add a user to it with this password 
```

# User docs 
https://docs.mattermost.com/guides/user.html


