from Jumpscale import j
from time import sleep


base = j.tools.prefab._getBaseClass()


class PrefabAlba(base):

    def _init(self):
        self.arakoon_version = 'a4e7dffc08cb999e1b1de45eb7f6efe8c978eb81'
        self.alba_version = '0.9.19'
        self.ocaml_version = '4.03.0'
        self.opam_root = None

    def build(self, start=True):
        self._install_deps()
        self._build()

    def _install_deps_opam(self):
        self.prefab.system.package.mdupdate()
        self.prefab.system.package.upgrade(distupgrade=True)

        apt_deps = """
        build-essential m4 apt-utils libffi-dev libssl-dev libbz2-dev libgmp3-dev libev-dev libsnappy-dev \
        libxen-dev help2man pkg-config time aspcud wget rsync darcs git unzip protobuf-compiler libgcrypt20-dev \
        libjerasure-dev yasm automake python-dev python-pip debhelper psmisc strace curl g++ libgflags-dev \
        sudo libtool libboost-all-dev fuse sysstat ncurses-dev librdmacm-dev
        """
        self.prefab.system.package.install(apt_deps, allow_unauthenticated=True)

        # OPAM
        self.opam_root = self.replace('$TMPDIR/OPAM')

        # profile fix
        if not self.prefab.core.file_exists('/root/.profile_js'):
            self.prefab.core.file_write('/root/.profile_js', "")

        # profile fix
        if not self.prefab.core.file_exists('/root/.profile_js'):
            self.prefab.core.file_write('/root/.profile_js', "")

        # self.prefab.core.run('wget https://raw.github.com/ocaml/opam/master/shell/opam_installer.sh')
        self.prefab.core.file_download(
            'https://raw.github.com/ocaml/opam/master/shell/opam_installer.sh', to='$TMPDIR/opam_installer.sh', minsizekb=0)
        self.prefab.core.run('sed -i "/read -p/d" $TMPDIR/opam_installer.sh')  # remove any confirmation
        self.prefab.core.run('bash $TMPDIR/opam_installer.sh $BINDIR %s' %
                              self.ocaml_version, profile=True, shell=True)

        cmd = 'opam init --root=%s --comp %s -a --dot-profile %s' % (
            self.opam_root, self.ocaml_version, self.prefab.bash.profilePath)
        self.prefab.core.run(cmd, profile=True, shell=True)

        janestreet = self.prefab.tools.git.pullRepo(
            'https://github.com/janestreet/opam-repository.git', depth=None, ssh=False)
        self.prefab.core.run(
            'cd %s && git pull && git checkout b98fd1964856f0c0b022a42ec4e6fc6c7bad2e81' % janestreet, shell=True)
        self.prefab.core.run("opam repo --root=%s -k local add janestreet %s || exit 0" %
                              (self.opam_root, janestreet), profile=True)

        cmd = "opam config env --root=%s --dot-profile %s > $TMPDIR/opam.env" % (
            self.opam_root, self.prefab.bash.profilePath)
        self.prefab.core.run(cmd, die=False, profile=True, shell=True)

        opam_deps = """oasis.0.4.6 ocamlfind ssl.0.5.2 camlbz2 snappy sexplib bisect lwt.2.5.2 \
        camltc.0.9.3 ocplib-endian.1.0 cstruct ctypes ctypes-foreign uuidm zarith mirage-no-xen.1 \
        quickcheck.1.0.2 cmdliner conf-libev depext kinetic-client tiny_json ppx_deriving \
        ppx_deriving_yojson core.114.05+21 redis.0.3.1 uri.1.9.2 result
        """

        self.prefab.core.run(
            'source $TMPDIR/opam.env && opam update && opam install -y %s' % opam_deps, profile=True)

    def _install_deps_intel_storage(self):
        url = 'https://01.org/sites/default/files/downloads/intelr-storage-acceleration-library-open-source-version/isa-l-2.14.0.tar.gz'
        self.prefab.core.file_download(url, to='$TMPDIR/isa-l-2.14.0.tar.gz')

        self.prefab.core.run('cd $TMPDIR && tar xfzv isa-l-2.14.0.tar.gz')
        self.prefab.core.run('cd $TMPDIR/isa-l-2.14.0 && ./autogen.sh && ./configure')
        self.prefab.core.run('cd $TMPDIR/isa-l-2.14.0 && make && make install')

        """
        RUN wget https://01.org/sites/default/files/downloads/intelr-storage-acceleration-library-open-source-version/isa-l-2.14.0.tar.gz
        RUN tar xfzv isa-l-2.14.0.tar.gz
        RUN cd isa-l-2.14.0 && ./autogen.sh && ./configure
        RUN cd isa-l-2.14.0 && make
        RUN cd isa-l-2.14.0 && make install
        """
        return

    def _install_deps_cpp(self):
        self.prefab.system.package.install("libgtest-dev cmake", allow_unauthenticated=True)
        self.prefab.core.run('cd /usr/src/gtest && cmake . && make && mv libg* /usr/lib/')

        """
        RUN apt-get update && apt-get -y install libgtest-dev cmake
        RUN cd /usr/src/gtest \
            && cmake . \
            && make \
            && mv libg* /usr/lib/
        """

        return

    def _install_deps_arakoon(self):
        aradest = self.prefab.tools.git.pullRepo(
            'https://github.com/openvstorage/arakoon.git', branch="1.9", depth=None, ssh=False)
        pfx = 'cd %s && source $TMPDIR/opam.env' % aradest

        self.prefab.core.run('%s && git pull && git checkout %s' % (pfx, self.arakoon_version), shell=True)
        self.prefab.core.run('%s && make' % pfx, shell=True)

        if self.prefab.core.file_exists('$TMPDIR/OPAM/4.03.0/lib/arakoon_client/META'):
            self.prefab.core.file_unlink('$TMPDIR/OPAM/4.03.0/lib/arakoon_client/META')

        prefix = '%s/%s' % (self.opam_root, self.ocaml_version)
        libdir = 'ocamlfind printconf destdir'
        cmd = '%s && export PREFIX=%s && export OCAML_LIBDIR=$(%s) && make install' % (pfx, prefix, libdir)

        self.prefab.core.run(cmd, profile=True)
        self.prefab.core.file_copy(j.sal.fs.joinPaths(aradest, 'arakoon.native'), "$BINDIR/arakoon")

        """
        RUN git clone https://github.com/openvstorage/arakoon.git
        RUN cd arakoon && git pull && git checkout tags/1.9.3
        RUN cd arakoon && eval `${opam_env}` && make
        RUN cd arakoon && eval `${opam_env}` \
            && export PREFIX=${opam_root}/${ocaml_version} \
            && export OCAML_LIBDIR=`ocamlfind printconf destdir` \
            && make install
        """
        return

    def _install_deps_orocksdb(self):
        #
        # cleaning
        #
        if self.prefab.core.file_exists('$TMPDIR/OPAM/%s/lib/rocks/META' % self.ocaml_version):
            self.logger.info('rocksdb already found')
            return

        if self.prefab.core.file_exists('/usr/local/lib/librocksdb.so'):
            self.prefab.core.run('rm -rfv /usr/local/lib/librocksdb.*')

        if self.prefab.core.dir_exists('/opt/code/github/domsj/orocksdb'):
            self.prefab.core.dir_remove('/opt/code/github/domsj/orocksdb', True)

        #
        # install
        #
        commit = '26c45963f1f305825785592efb41b50192a07491'
        orodest = self.prefab.tools.git.pullRepo('https://github.com/domsj/orocksdb.git', depth=None, ssh=False)

        pfx = 'cd %s && source $TMPDIR/opam.env' % orodest
        self.prefab.core.run('%s && git pull && git checkout %s' % (pfx, commit))

        self.prefab.core.run('%s && ./install_rocksdb.sh && make build install' % pfx)

        """
        RUN git clone https://github.com/domsj/orocksdb.git \
            && eval `${opam_env}` \
            && cd orocksdb \
            && git checkout 8bc61d8a451a2724399247abf76643aa7b2a07e9 \
            && ./install_rocksdb.sh \
            && make build install
        """
        return

    def _install_deps_sources(self):
        self.prefab.core.file_write('/etc/apt/sources.list.d/wily-universe.list',
                                     "deb http://archive.ubuntu.com/ubuntu/ wily universe\n")
        self.prefab.core.file_write('/etc/apt/sources.list.d/ovsaptrepo.list',
                                     "deb http://apt.openvstorage.org unstable main\n")
        self.prefab.system.package.mdupdate()

        apt_deps = """
        librdmacm-dev clang-3.5 liblttng-ust0 librdmacm1 libtokyocabinet9 libstdc++6:amd64 libzmq3 \
        librabbitmq1 libomnithread3c2 libomniorb4-1 libhiredis0.13 liblz4-1 libxio-dev libxio0 \
        omniorb-nameserver libunwind8-dev libaio1 libaio1-dbg libaio-dev libz-dev libbz2-dev \
        libgoogle-glog-dev libibverbs-dev"""

        self.prefab.system.package.install(apt_deps, allow_unauthenticated=True)

    def _install_deps_ordma(self):
        #
        # cleaning
        #
        if self.prefab.core.file_exists('$TMPDIR/OPAM/%s/lib/ordma/META' % self.ocaml_version):
            self.logger.info('ordma already found')
            return

        #
        # install
        #
        commit = 'tags/0.0.2'
        ordmadest = self.prefab.tools.git.pullRepo(
            'https://github.com/toolslive/ordma.git', depth=None, ssh=False)

        self.prefab.core.run('cd %s && git pull && git fetch --tags && git checkout %s' % (ordmadest, commit))

        pfx = 'cd %s && source $TMPDIR/opam.env' % ordmadest
        self.prefab.core.run('%s && eval `${opam_env}` && make install' % pfx)

        """
        RUN git clone https://github.com/toolslive/ordma.git \
            && cd ordma \
            && git checkout tags/0.0.2 \
            && eval `${opam_env}` \
            && make install
        """
        pass

    def _install_deps_gobjfs(self):
        commit = '3b591baf7518987ce1b6c828865f0089007281e4'
        gobjfsdest = self.prefab.tools.git.pullRepo(
            'https://github.com/openvstorage/gobjfs.git', depth=None, ssh=False)

        self.prefab.core.run('cd %s && git pull && git fetch --tags && git checkout %s' % (gobjfsdest, commit))
        self.prefab.core.run(
            'cd %s && mkdir -p build && cd build && cmake -DCMAKE_BUILD_TYPE=RELWITHDEBINFO ..' % gobjfsdest)
        self.prefab.core.run('cd %s/build && make && make install' % gobjfsdest)

        """
        RUN git clone https://github.com/openvstorage/gobjfs.git
        RUN cd gobjfs  && git pull && git checkout 3b591baf7518987ce1b6c828865f0089007281e4
        RUN cd gobjfs \
               && mkdir build \
               && cd build \
               && cmake -DCMAKE_BUILD_TYPE=RELWITHDEBINFO .. \
               && make \
               && make install
        """
        pass

    def _install_deps_etcd(self):
        url = 'https://github.com/coreos/etcd/releases/download/v2.2.4/etcd-v2.2.4-linux-amd64.tar.gz'
        self.prefab.core.file_download(url, to='$TMPDIR/etcd-v2.2.4-linux-amd64.tar.gz')

        self.prefab.core.run('cd $TMPDIR && tar xfzv etcd-v2.2.4-linux-amd64.tar.gz')
        self.prefab.core.run('cp $TMPDIR/etcd-v2.2.4-linux-amd64/etcd /usr/bin')
        self.prefab.core.run('cp $TMPDIR/etcd-v2.2.4-linux-amd64/etcdctl /usr/bin')

        """
        RUN curl -L  https://github.com/coreos/etcd/releases/download/v2.2.4/etcd-v2.2.4-linux-amd64.tar.gz -o etcd-v2.2.4-linux-amd64.tar.gz
        RUN tar xzvf etcd-v2.2.4-linux-amd64.tar.gz
        RUN cp ./etcd-v2.2.4-linux-amd64/etcd /usr/bin \
            && cp ./etcd-v2.2.4-linux-amd64/etcdctl /usr/bin
        """

        return

    def _install_deps(self):
        self._install_deps_opam()
        self._install_deps_intel_storage()
        self._install_deps_cpp()
        self._install_deps_arakoon()
        self._install_deps_orocksdb()
        self._install_deps_sources()
        self._install_deps_ordma()
        self._install_deps_gobjfs()
        self._install_deps_etcd()

    def _build(self):
        repo = self.prefab.tools.git.pullRepo('https://github.com/openvstorage/alba', depth=None, ssh=False)

        self.prefab.core.run('cd %s && git checkout %s' % (repo, self.alba_version))

        self.prefab.core.run('source $TMPDIR/opam.env && cd %s; make' % repo, profile=True)
        self.prefab.core.file_copy('%s/ocaml/alba.native' % repo, '$BINDIR/alba')
        self.prefab.core.file_copy('%s/ocaml/albamgr_plugin.cmxs' % repo, '$BINDIR/albamgr_plugin.cmxs')
        self.prefab.core.file_copy('%s/ocaml/nsm_host_plugin.cmxs' % repo, '$BINDIR/nsm_host_plugin.cmxs')
        self.prefab.core.file_copy('%s/ocaml/disk_failure_tests.native' % repo, '$BINDIR/disk_failure_tests.native')
