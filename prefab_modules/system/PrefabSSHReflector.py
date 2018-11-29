
from Jumpscale import j
import os
import time

import socket

base = j.tools.prefab._getBaseClass()


class PrefabSSHReflector(base):

    def __init__(self, executor, prefab):
        self.executor = executor
        self.prefab = prefab

    def server(self, reset=False, keyname="reflector"):
        """
        configurs the server
        to test
        js 'c=j.tools.prefab.get("stor1:9022");c.installer.sshreflector.server'
        """

        port = 9222

        package = "dropbear"
        self.prefab.system.package.install(package)

        self.prefab.core.run("rm -f /etc/default/dropbear", die=False)
        self.prefab.core.run("killall dropbear", die=False)

        passwd = j.data.idgenerator.generateGUID()
        self.prefab.user.ensure("sshreflector", passwd=passwd, home="/home/sshreflector",
                                uid=None, gid=None, shell=None, fullname=None, encrypted_passwd=True, group=None)

        self.prefab.core.run('ufw allow %s' % port, die=False)

        self.prefab.core.dir_ensure("/home/sshreflector/.ssh", recursive=True, mode=None,
                                    owner="sshreflector", group="sshreflector")

        lpath = os.environ["HOME"] + "/.ssh/reflector"
        path = "/home/sshreflector/.ssh/reflector"
        ftp = self.prefab.core.executor.sshclient.sftp
        if j.sal.fs.exists(lpath) and j.sal.fs.exists(lpath + ".pub"):
            self.logger.info("UPLOAD EXISTING SSH KEYS")
            ftp.put(lpath, path)
            ftp.put(lpath + ".pub", path + ".pub")
        else:
            # we do the generation of the keys on the server
            if reset or not self.prefab.core.file_exists(path) or not self.prefab.core.file_exists(path + ".pub"):
                self.prefab.core.file_unlink(path)
                self.prefab.core.file_unlink(path + ".pub")
                #-N is passphrase
                self.prefab.core.run("ssh-keygen -q -t rsa -b 4096 -f %s -N '' " % path)
            ftp.get(path, lpath)
            ftp.get(path + ".pub", lpath + ".pub")

            j.sal.fs.chmod(lpath, 0o600)
            j.sal.fs.chmod(lpath + ".pub", 0o600)

        # authorize remote server to accept now copied private key
        self.prefab.system.ssh.authorize("sshreflector", j.sal.fs.fileGetContents(lpath + ".pub"))

        self.prefab.core.run("chmod 0644 /home/sshreflector/.ssh/*")
        self.prefab.core.run("chown -R sshreflector:sshreflector /home/sshreflector/.ssh/")

        _, cpath, _ = self.prefab.core.run("which dropbear")

        cmd = "%s -R -F -E -p 9222 -w -s -g -K 20 -I 60" % cpath
        # self.prefab.system.processmanager.e
        pm = self.prefab.system.processmanager.get()
        pm.ensure("reflector", cmd)

        # self.prefab.system.package.start(package)

        self.prefab.system.ns.hostfile_set_fromlocal()

        if self.prefab.system.process.tcpport_check(port, "dropbear") is False:
            raise j.exceptions.RuntimeError("Could not install dropbear, port %s was not running" % port)

    #
    def client_delete(self):
        self.prefab.system.processmanager.remove("autossh")  # make sure leftovers are gone
        self.prefab.core.run("killall autossh", die=False, showout=False)

    def client(self, remoteids, reset=True):
        """
        chose a port for remote server which we will reflect to
        @param remoteids :  ovh4,ovh5:2222

        to test
        js 'c=j.tools.prefab.get("192.168.0.149");c.installer.sshreflector_client("ovh4,ovh5:2222")'

        """

        if remoteids.find(",") != -1:
            for item in remoteids.split(","):
                self.prefab.sshreflector.client(item.strip())
        else:

            self.client_delete()

            self.prefab.system.ns.hostfile_set_fromlocal()

            remoteprefab = j.tools.prefab.get(remoteids)

            package = "autossh"
            self.prefab.system.package.install(package)

            lpath = os.environ["HOME"] + "/.ssh/reflector"

            if reset or not j.sal.fs.exists(lpath) or not j.sal.fs.exists(lpath_pub):
                self.logger.info("DOWNLOAD SSH KEYS")
                # get private key from reflector
                ftp = remoteprefab.core.executor.sshclient.sftp
                path = "/home/sshreflector/.ssh/reflector"
                ftp.get(path, lpath)
                ftp.get(path + ".pub", lpath + ".pub")
                ftp.close()

            # upload to reflector client
            ftp = self.prefab.core.executor.sshclient.sftp
            rpath = "/root/.ssh/reflector"
            ftp.put(lpath, rpath)
            ftp.put(lpath + ".pub", rpath + ".pub")
            self.prefab.core.run("chmod 0600 /root/.ssh/reflector")
            self.prefab.core.run("chmod 0600 /root/.ssh/reflector.pub")

            if(remoteprefab.core.executor.addr.find(".") != -1):
                # is real ipaddress, will put in hostfile as reflector
                addr = remoteprefab.core.executor.addr
            else:
                a = socket.gethostbyaddr(remoteprefab.core.executor.addr)
                addr = a[2][0]

            port = remoteprefab.core.executor.port

            # test if we can reach the port
            if j.sal.nettools.tcpPortConnectionTest(addr, port) is False:
                raise j.exceptions.RuntimeError("Cannot not connect to %s:%s" % (addr, port))

            rname = "refl_%s" % remoteprefab.core.executor.addr.replace(".", "_")
            rname_short = remoteprefab.core.executor.addr.replace(".", "_")

            self.prefab.system.ns.hostfile_set(rname, addr)

            if remoteprefab.core.file_exists("/home/sshreflector/reflectorclients") is False:
                self.logger.info("reflectorclientsfile does not exist")
                remoteprefab.core.file_write("/home/sshreflector/reflectorclients", "%s:%s\n" %
                                             (self.prefab.platformtype.hostname, 9800))
                newport = 9800
                out2 = remoteprefab.core.file_read("/home/sshreflector/reflectorclients")
            else:
                remoteprefab.core.file_read("/home/sshreflector/reflectorclients")
                out = remoteprefab.core.file_read("/home/sshreflector/reflectorclients")
                out2 = ""
                newport = 0
                highestport = 0
                for line in out.split("\n"):
                    if line.strip() == "":
                        continue
                    if line.find(self.prefab.platformtype.hostname) != -1:
                        newport = int(line.split(":")[1])
                        continue
                    foundport = int(line.split(":")[1])
                    if foundport > highestport:
                        highestport = foundport
                    out2 += "%s\n" % line
                if newport == 0:
                    newport = highestport + 1
                out2 += "%s:%s\n" % (self.prefab.platformtype.hostname, newport)
                remoteprefab.core.file_write("/home/sshreflector/reflectorclients", out2)

            self.prefab.core.file_write("/etc/reflectorclients", out2)

            reflport = "9222"

            self.logger.info("check ssh connection to reflector")
            self.prefab.core.run(
                "ssh -i /root/.ssh/reflector -o StrictHostKeyChecking=no sshreflector@%s -p %s 'ls /'" %
                (rname, reflport))
            self.logger.info("OK")

            _, cpath, _ = self.prefab.core.run("which autossh")
            cmd = "%s -M 0 -N -o ExitOnForwardFailure=yes -o \"ServerAliveInterval 60\" -o \"ServerAliveCountMax 3\" -R %s:localhost:22 sshreflector@%s -p %s -i /root/.ssh/reflector" % (
                cpath, newport, rname, reflport)

            pm = self.prefab.system.processmanager.get()
            pm.ensure("autossh_%s" % rname_short, cmd, descr='')

            self.logger.info("On %s:%s remote SSH port:%s" % (remoteprefab.core.executor.addr, port, newport))

    def createconnection(self, remoteids):
        """
        @param remoteids are the id's of the reflectors e.g. 'ovh3,ovh5:3333'
        """
        self.prefab.core.run("killall autossh", die=False)
        self.prefab.system.package.install("autossh")

        if remoteids.find(",") != -1:
            prefab = None
            for item in remoteids.split(","):
                try:
                    prefab = j.tools.prefab.get(item)
                except BaseException:
                    pass
        else:
            prefab = j.tools.prefab.get(remoteids)
        if prefab is None:
            raise j.exceptions.RuntimeError("could not find reflector active")

        rpath = "/home/sshreflector/reflectorclients"
        lpath = os.environ["HOME"] + "/.ssh/reflectorclients"
        ftp = prefab.core.executor.sshclient.sftp
        ftp.get(rpath, lpath)

        out = self.prefab.core.file_read(lpath)

        addr = prefab.core.executor.addr

        keypath = os.environ["HOME"] + "/.ssh/reflector"

        for line in out.split("\n"):
            if line.strip() == "":
                continue
            name, port = line.split(":")

            # cmd="ssh sshreflector@%s -o StrictHostKeyChecking=no -p 9222 -i %s -L %s:localhost:%s"%(addr,keypath,port,port)
            # self.prefab.tmux.executeInScreen("ssh",name,cmd)

            cmd = "autossh -M 0 -N -f -o ExitOnForwardFailure=yes -o \"ServerAliveInterval 60\" -o \"ServerAliveCountMax 3\" -L %s:localhost:%s sshreflector@%s -p 9222 -i %s" % (
                port, port, addr, keypath)
            self.prefab.core.run(cmd)

        self.logger.info("\n\n\n")
        self.logger.info("Reflector:%s" % addr)
        self.logger.info(out)

    def __str__(self):
        return "prefab.reflector:%s:%s" % (getattr(self.executor, 'addr', 'local'),
                                           getattr(self.executor, 'port', ''))

    __repr__ = __str__
