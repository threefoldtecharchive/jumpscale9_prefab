
from js9 import j
from JumpScale9.sal.fs.SystemFS import FileLock
from JumpScale9Prefab.PrefabPackage import LOCK_NAME, LOCK_TIMEOUT
import random

app = j.tools.prefab._getBaseAppClass()


class PrefabDocker(app):
    NAME = "docker"

    def _init_docker(self):
        try:
            self.prefab.core.run("service docker start")
        except Exception as e:
            if 'cgroup is already mounted' in e.__str__():
                return
            raise e

    def install(self, reset=False):
        if reset is False and self.isInstalled():
            return
        if self.prefab.core.isUbuntu:
            self.prefab.bash.envSet('LC_ALL', 'C.UTF-8')
            self.prefab.bash.envSet('LANG', 'C.UTF-8')
            if not self.prefab.core.command_check('docker'):
                C = """
                wget -qO- https://get.docker.com/ | sh
                """
                with FileLock(LOCK_NAME, locktimeout=LOCK_TIMEOUT):
                    self.prefab.core.run(C)
             # if not self.prefab.core.command_check('docker-compose'):
            #     C = """
            #     curl -L https://github.com/docker/compose/releases/download/1.8.0-rc1/docker-compose-`uname -s`-`uname -m` > /usr/local/bin/docker-compose
            #     chmod +x /usr/local/bin/docker-compose
            #     """
            #     self.prefab.core.run(C)
        if self._prefab.core.isArch:
            self.prefab.package.install("docker")
            # self.prefab.package.install("docker-compose")
        self._init_docker()

    def ubuntuBuild(self, push=False):
        self._init_docker()
        dest = self.prefab.development.git.pullRepo('https://github.com/Jumpscale/dockers.git', ssh=False)
        path = self.prefab.core.joinpaths(dest, 'js8/x86_64/01_ubuntu1604')

        C = """
        set -ex
        cd %s
        docker build -t jumpscale/ubuntu1604 --no-cache .
        """ % path
        self.prefab.core.execute_bash(C)

        if push:
            C = """
            set -ex
            cd %s
            docker push jumpscale/ubuntu1604
            """ % path
            self.prefab.core.execute_bash(C)

    def resetPasswd(self, dockerPrefabObject):
        # change passwd
        dockerPrefabObject.user.passwd("root", j.data.idgenerator.generateGUID())

    def dockerStart(self, name="ubuntu1", image='jumpscale/ubuntu1604',
                    ports='', volumes=None, pubkey=None, weave=False, ssh=True, weavePeer=None):
        """
        will return dockerPrefabObj: is again a prefab obj on which all kinds of actions can be executed

        @param ports e.g. 2022,2023
        @param volumes e.g. format: "/var/insidemachine:/var/inhost # /var/1:/var/1
        @param ports e.g. format "22:8022 80:8080"  the first arg e.g. 22 is the port in the container
        @param weave If weave is available on node, weave will be used by default. To make sure weave is available, set to True

        """
        if weave:
            self.prefab.systemservices.weave.install(start=True, peer=weavePeer)

        self._init_docker()

        if ssh and '22:' not in ports:
            port = "2202"
            while port in ports:
                port = random.randint(1000, 9999)
            ports += '22:%s' % port

        cmd = "jsdocker create --name {name} --image {image}".format(name=name, image=image)
        if pubkey:
            cmd += " --pubkey '%s'" % pubkey
        if ports:
            cmd += " --ports '%s'" % ports
        if volumes:
            cmd += " --volumes '%s'" % volumes
        # if aydofs:
        #     cmd += " --aysfs"
        self.prefab.core.run(cmd, profile=True)
        cmd = "jsdocker list --name {name} --parsable".format(name=name)
        _, out, _ = self.prefab.core.run(cmd, profile=True)
        # FIXME: cannot find g8core is included to the output
        #out = out.replace("cannot find g8core\n","")

        info = j.data.serializer.json.loads(out)

        port = info[0]["port"]
        #host = info[0]["host"]
        _, out, _ = self.prefab.core.run(
            "docker inspect {name} | grep \"IPAddress\"|  cut -d '\"' -f 4 ".format(name=name))
        host = out
        dockerexecutor = Prefabdockerobj(name, host, "22", self.prefab)
        prefabdockerobj = j.tools.prefab.get(dockerexecutor)

        # NEED TO MAKE SURE WE CAN GET ACCESS TO THIS DOCKER WITHOUT OPENING PORTS; we know can using docker exec
        # ON DOCKER HOST (which is current prefab)

        return prefabdockerobj

    def getDocker(self, name):
        pass


class Prefabdockerobj:

    def __init__(self, name, addr, port, prefabDockerHost):
        self.id = 'docker:%s:%s' % (prefabDockerHost.id, name)
        self.addr = addr
        self.port = port
        self.name = name
        self.login = "root"
        self.prefabDockerHost = prefabDockerHost
        self._prefab = None
        self.CURDIR = "/root"  # required by PrefabFactory
        self.env = {}  # required by prefabFactory

    def execute(self, cmds, die=True, checkok=None, async=False, showout=True, timeout=0, env={}):
        return self.prefabDockerHost.core.run(
            "docker exec %s bash -c '%s'" %
            (self.name,
             cmds.replace(
                 "'",
                 "'\"'\"'")),
            die=die,
            checkok=checkok,
            showout=showout,
            env=env)

    executeRaw = execute

    @property
    def prefab(self):
        if not self._prefab:
            self._prefab = j.tools.prefab.get(self)
        return self._prefab


# def archBuild(self):
#     C = """
#     FROM base/archlinux:latest

#
# def archBuild(self):
#     C = """
#     FROM base/archlinux:latest
#
#     MAINTAINER "Matthias Adler" <macedigital@gmail.com> / kristof de spiegeleer
#
#     RUN pacman -S --debug --noconfirm archlinux-keyring
#
#     RUN pacman -S --needed --noconfirm git iproute2 iputils procps-ng tar which licenses util-linux
#     RUN pacman -S --noconfirm curl wget ssh  mc
#
#
#     # remove unneeded pkgs, update and clean cache
#     # RUN pacman -Rss --noconfirm cronie device-mapper dhcpcd diffutils file nano vi texinfo usbutils gcc pinentry; \
#
#     # RUN pacman -Syu --force --noconfirm; pacman -Scc --noconfirm
#
#     # remove man pages and locale data
#     RUN rm -rf /archlinux/usr/share/locale && rm -rf /archlinux/usr/share/man
#
#     # clean unneeded services
#     RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
#     rm -f /lib/systemd/system/multi-user.target.wants/*;\
#     rm -f /lib/systemd/system/graphical.target.wants/*; \
#     rm -f /etc/systemd/system/*.wants/*;\
#     rm -f /lib/systemd/system/local-fs.target.wants/*; \
#     rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
#     rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
#     rm -f /lib/systemd/system/basic.target.wants/*;\
#     rm -f /lib/systemd/system/anaconda.target.wants/*;
#
#     # switch default target from graphical to multi-user
#     RUN systemctl set-default multi-user.target
#
#     # systemd inside a container
#     ENV container docker
#     VOLUME [ "/sys/fs/cgroup" ]
#
#     CMD ["/usr/sbin/init"]
#
#     """
#     self.prefab.core.run("rm -rf $TMPDIR/docker;mkdir $TMPDIR/docker")
#     self.prefab.core.file_write("$TMPDIR/docker/Dockerfile", C)
#
#     C = """
#     set -ex
#     cd $TMPDIR/docker
#     docker build -t arch .
#     """
#     self.prefab.core.execute_bash(C)
