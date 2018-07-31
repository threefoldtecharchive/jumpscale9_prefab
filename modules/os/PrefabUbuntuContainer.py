from jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabChroot(base):

    def __init__(self, prefab):
        self.prefab = prefab
        self.path = '/tmp/{}'.format(j.data.idgenerator.generateGUID())

    def __enter__(self):
        self.prefab.core.dir_ensure(self.path + '/proc')
        self.prefab.core.dir_ensure(self.path + '/dev')
        self.prefab.core.dir_ensure(self.path + '/sys')
        self.prefab.core.run('mount -o bind /proc {}/proc'.format(self.path))
        self.prefab.core.run('mount -o bind /dev {}/dev'.format(self.path))
        self.prefab.core.run('mount -o bind /sys {}/sys'.format(self.path))
        return self

    def __exit__(self, *args):
        self.prefab.core.run('umount {}/proc'.format(self.path))
        self.prefab.core.run('umount {}/dev'.format(self.path))
        self.prefab.core.run('umount {}/sys'.format(self.path))

    def install_ubuntu(self, distro='xenial'):
        self.prefab.core.dir_ensure(self.path)
        self.prefab.core.command_ensure('debootstrap')
        self.prefab.core.run('debootstrap {} {} http://ftp.belnet.be/ubuntu.com/ubuntu'.format(distro, self.path), timeout=3600)
        sources = '''\
deb http://archive.ubuntu.com/ubuntu/ {0} main universe multiverse restricted
'''.format(distro)
        self.write_file('/etc/apt/sources.list', sources)
        locales = '''\
en_US.UTF-8 UTF-8
en_GB.UTF-8 UTF-8
'''
        self.write_file('/etc/locale.gen', locales)

    def execute(self, cmd):
        cmd = "chroot {} bash -c '{}'".format(self.path, cmd)
        self.prefab.core.run(cmd)

    def write_file(self, path, content):
        path = self.path + path
        self.prefab.core.file_write(path, content)

    def append_file(self, path, content):
        path = self.path + path
        self.prefab.core.file_write(path, content, append=True)


class PrefabUbuntuContainer(base):

    def build_flist(self, dist, passwd, jwt=None, ssh_autostart=False):
        """
        build an ubuntu flist used to deploy 0-os container

        [description]

        :param dist: ubuntu distribution name (xenial, bionic, ...)
        :type dist: string
        :param passwd: root password
        :type passwd: string
        :param jwt: jwt used to push the generated flist to the hub, if None flist will not be pushed, defaults to None
        :param jwt: string, optional
        :param ssh_autostart: if True, the flist will contain a startup file that will
                              automatically start openssh server when deployed, defaults to False
        :param ssh_autostart: bool, optional
        :return: path to the tar file generated. This tar can be pushed to the 0-hub
        :rtype: string
        """
        chroot = PrefabChroot(self.prefab)
        chroot.install_ubuntu(dist)
        with chroot:
            chroot.append_file('/root/.bashrc', 'export PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin/:/usr/local/sbin:/usr/bin/site_perl:/usr/bin/vendor_perl:/usr/bin/core_perl')
            chroot.execute('locale-gen')
            chroot.write_file('/etc/hostname', 'ubuntu')
            chroot.write_file('/etc/resolv.conf', 'nameserver 8.8.8.8')
            chroot.execute('mkdir /var/run/sshd')
            chroot.execute('apt-get update')
            chroot.execute('apt-get install -y --allow-unauthenticated --no-install-recommends build-essential git vim mc openssh-server linux-generic wget ca-certificates curl')
            chroot.execute('echo "root:{}" | chpasswd'.format(passwd))

            if ssh_autostart is True:
                chroot.write_file('/.startup.toml', _startup)
                chroot.execute("sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config")

        tarfile = '/tmp/ubuntu-{}.tar.gz'.format(dist)
        self.prefab.core.dir_remove('{}/var/apt/cache/archives'.format(chroot.path))
        self.prefab.core.run('tar czpf {} -C {} --exclude tmp --exclude dev --exclude sys --exclude proc .'.format(tarfile, chroot.path))

        if jwt:
            self.prefab.core.run('curl -b "caddyoauth={}" -F file=@{} https://hub.gig.tech/api/flist/me/upload'.format(jwt, tarfile))

        self.prefab.core.dir_remove(chroot.path)
        return tarfile


_startup = """
[startup.sshd]
name = "bash"

[startup.sshd.args]
script = \"""
dpkg-reconfigure openssh-server
chmod 0700 /etc/ssh/ssh_host_*
/usr/sbin/sshd
\"""
"""
