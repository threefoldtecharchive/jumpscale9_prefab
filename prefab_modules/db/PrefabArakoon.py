from Jumpscale import j

base = j.tools.prefab._getBaseClass()


class PrefabArakoon(base):

    def _build(self):
        exists = self.prefab.core.command_check("arakoon")

        if exists:
            cmd = self.prefab.core.command_location("arakoon")
            dest = "%s/arakoon" % self.prefab.core.dir_paths["BINDIR"]
            if j.sal.fs.pathClean(cmd) != j.sal.fs.pathClean(dest):
                self.prefab.core.file_copy(cmd, dest)
        else:
            arakoon_url = 'https://github.com/openvstorage/arakoon.git'
            dest = self.prefab.tools.git.pullRepo(arakoon_url)
            self.prefab.core.run('cd %s && git pull && git fetch --tags && git checkout tags/1.9.7' % dest)

            cmd = 'cd %s && make' % (dest)
            self.prefab.core.run(cmd, profile=True)

            self.prefab.core.file_copy('%s/arakoon.native' % dest, "{DIR_BIN}/arakoon", overwrite=True)

        self.prefab.core.dir_ensure('{DIR_VAR}/data/arakoon')

    def _install_ocaml(self):
        self._logger.info("download opam installer")
        ocaml_url = 'https://raw.github.com/ocaml/opam/master/shell/opam_installer.sh'
        self.prefab.core.file_download(ocaml_url, to='{DIR_TEMP}/opam_installer.sh')
        self._logger.info("install opam")
        self.prefab.core.run('chmod +x {DIR_TEMP}/opam_installer.sh')
        ocaml_version = '4.02.3'
        cmd = 'yes | {DIR_TEMP}/opam_installer.sh {DIR_BIN} %s' % ocaml_version
        self.prefab.core.run(cmd, profile=True)

        self._logger.info("initialize opam")
        opam_root = self.executor.replace('{DIR_TEMP}/OPAM')
        self.prefab.core.dir_ensure(opam_root)
        cmd = 'opam init --root=%s --comp %s -a --dot-profile %s' % (
            opam_root, ocaml_version, self.prefab.bash.profilePath)
        self.prefab.core.run(cmd, profile=True)

        cmd = "opam config env --root=%s --dot-profile %s" % (opam_root, self.prefab.bash.profilePath)
        self.prefab.core.run(cmd, profile=True)

        opam_deps = (
            'ocamlfind',
            'ssl',
            'camlbz2',
            'snappy',
            'sexplib',
            'bisect',
            'lwt.2.5.1',
            'camltc',
            'cstruct',
            'ctypes-foreign',
            'zarith',
            'mirage-no-xen.1',
            'quickcheck.1.0.2',
            'cmdliner',
            'conf-libev',
            'depext',
            'tiny_json',
            'ppx_deriving.3.1',
            'ppx_deriving_yojson',
            'core.113.00.00',
            'uri.1.9.1',
            'result',
            'ocplib-endian'
        )

        self._logger.info("start installation of ocaml pacakges")
        cmd = 'opam update && opam install -y {}'.format(' '.join(opam_deps))
        self.prefab.core.run(cmd, profile=True)
        # For some reason redis failed when added to the others but success on its own
        self.prefab.core.run('opam update && opam install -y redis', profile=True)

    def _install_deps(self):
        apt_deps = (
            'curl',
            'make',
            'm4',
            'gcc',
            'patch',
            'unzip',
            'git',
            'pkg-config',
            'libprotobuf9v5',
            'libprotoc9v5',
            'protobuf-compiler',
            'libsnappy-dev',
            'libssl-dev',
            'libssl-doc',
            'zlib1g-dev',
            'bzip2-doc',
            'libbz2-dev',
            'libncurses5-dev',
            'libtinfo-dev',
            'libgmp-dev',
            'libgmpxx4ldbl',
            'libev-dev',
            'libev4'
        )
        self.prefab.system.package.install(apt_deps)

    def build(self, start=True):
        self._install_deps()
        self._install_ocaml()
        self._build()
        if start:
            self.start()

    def start(self):
        which = self.prefab.core.command_location("arakoon")
        self.prefab.core.dir_ensure('{DIR_VAR}/data/arakoon')
        cmd = "%s --config {DIR_BASE}/cfg/arakoon/arakoon.ini" % which
        self.prefab.system.process.kill("arakoon")
        pm = self.prefab.system.processmanager.get()
        pm.ensure("arakoon", cmd=cmd, env={}, path="")

    def create_cluster(self, id):
        return ArakoonCluster(id, self.prefab)


class ArakoonNode(object):

    def __init__(self, ip, home, client_port, messaging_port, log_level):
        super(ArakoonNode, self).__init__()
        self.id = ''
        self.ip = ip
        self.home = j.sal.fs.pathClean(home)
        self.client_port = client_port
        self.messaging_port = messaging_port
        self.log_level = log_level


class ArakoonCluster(object):

    def __init__(self, id, prefab):
        super(ArakoonCluster, self).__init__()
        self.id = id
        self.prefab = prefab
        self.plugins = []
        self.nodes = []

    def add_node(self, ip, home='{DIR_VAR}/data/arakoon', client_port=7080, messaging_port=10000, log_level='info'):
        home = self.executor.replace(home)
        node = ArakoonNode(ip=ip, home=home, client_port=client_port,
                           messaging_port=messaging_port, log_level=log_level)
        node.id = 'node_%d' % len(self.nodes)
        self.nodes.append(node)
        return node

    def get_config(self):
        tmp = j.sal.fs.getTempFileName()
        f = j.tools.inifile.new(tmp)

        f.addSection('global')
        _cluster = ''
        for node in self.nodes:
            _cluster += '%s, ' % node.id
        _cluster = _cluster[:-2]
        f.addParam('global', 'cluster', _cluster)
        f.addParam('global', 'cluster_id', self.id)
        if len(self.plugins) > 0:
            plugins = ', '.join(self.plugins)
            f.addParam('plugins', plugins)

        for node in self.nodes:
            f.addSection(node.id)
            f.addParam(node.id, 'ip', node.ip)
            f.addParam(node.id, 'client_port', node.client_port)
            f.addParam(node.id, 'messaging_port', node.messaging_port)
            f.addParam(node.id, 'home', node.home)
            f.addParam(node.id, 'log_level', node.log_level)

        f.write()
        content = j.sal.fs.readFile(tmp)
        j.sal.fs.remove(tmp)
        return content


if __name__ == '__main__':
    c = j.tools.prefab.local
    cluster = c.apps.arakoon.create_cluster('test')
    node1 = cluster.add_node('127.0.0.1')
    node2 = cluster.add_node('172.20.0.55')
    cfg = cluster.get_config()
    self._logger.info(cfg)
