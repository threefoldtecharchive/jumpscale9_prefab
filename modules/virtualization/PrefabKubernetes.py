
import time
from js9 import j

app = j.tools.prefab._getBaseAppClass()
OPENSSL = """
[ req ]
distinguished_name = req_distinguished_name
[req_distinguished_name]
[ v3_ca ]
basicConstraints = critical, CA:TRUE
keyUsage = critical, digitalSignature, keyEncipherment, keyCertSign
[ v3_req_etcd ]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names_etcd
[ alt_names_etcd ]
{alt_names_etcd}
"""

ETCD_SERVICE = """
[Unit]
Description=etcd
Documentation=https://github.com/coreos

[Service]
ExecStart=$BINDIR/etcd \\
  --name {name} \\
  --cert-file=$CFGDIR/etcd/pki/etcd.crt \\
  --key-file=$CFGDIR/etcd/pki/etcd.key \\
  --peer-cert-file=$CFGDIR/etcd/pki/etcd-peer.crt \\
  --peer-key-file=$CFGDIR/etcd/pki/etcd-peer.key \\
  --trusted-ca-file=$CFGDIR/etcd/pki/etcd-ca.crt \\
  --peer-trusted-ca-file=$CFGDIR/etcd/pki/etcd-ca.crt \\
  --peer-client-cert-auth \\
  --client-cert-auth \\
  --initial-advertise-peer-urls https://{node_ip}:2380 \\
  --listen-peer-urls https://{node_ip}:2380 \\
  --listen-client-urls https://{node_ip}:2379,http://127.0.0.1:2379 \\
  --advertise-client-urls https://{node_ip}:2379 \\
  --initial-cluster-token etcd-cluster-0 \\
  --initial-cluster {initial_cluster} \\
  --data-dir=/var/lib/etcd
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

KUBE_INIT = """
apiVersion: kubeadm.k8s.io/v1alpha1
kind: MasterConfiguration
api:
  advertiseAddress: {node_ip}
  bindPort: 6443
authorizationMode: Node,RBAC
etcd:
  endpoints:
{endpoints}
  caFile: $CFGDIR/etcd/pki/etcd-ca.crt
  certFile: $CFGDIR/etcd/pki/etcd.crt
  keyFile: $CFGDIR/etcd/pki/etcd.key
  dataDir: /var/lib/etcd
  etcdVersion: v3.2.9
networking:
  podSubnet: {flannel_subnet}
apiServerCertSANs:
{external_ips}

certificatesDir: /etc/kubernetes/pki/
"""


class PrefabKubernetes(app):
    """
    Prefab that allows deployment of kubernetes cluster or adding new nodes to an existing cluster
    """
    NAME = "kubectl"

    def minikube_install(self, reset=False):
        """
        install full minikube, only support ubuntu 16.04+ (check this)
        """

        if self.doneCheck("minikube_install", reset):
            return

        self.install_dependencies()

        self.doneSet("minikube_install")

    def multihost_install(self, nodes=[], external_ips=[], unsafe=False, reset=False):
        """
        Important !! only supports centos, fedora and ubuntu 1604
        Use a list of prefab connections where all nodes need to be reachable from all other nodes or at least from the master node.
        this installer will:
        - use first node as master
        - deploy/generate required secrets/keys to allow user to access this kubernetes
        - make sure that dashboard is installed as well on kubernetes
        - use /storage inside the node (make sure is btrfs partition?) as the backend for kubernetes
        - deploy zerotier network (optional) into the node which connects to the kubernetes (as pub network?)

        @param nodes ,,  are list of prefab clients which will be used to deploy kubernetes
        @param external_ips,,list(str) list of extra ips to add to certs
        @param unsafe,, bool will allow pods to be created on master nodes.
        @param reset ,, rerun the code even if it has been run again. this may not be safe (used for development only)
        @return (dict(), str) ,, return the kubelet config as a dict write as yaml file to any kubectl that need to control the cluster

        """
        if self.doneCheck("multihost_install", reset):
            return

        if unsafe:
            masters, nodes = nodes, []
        else:
            masters, nodes = nodes[:3], nodes[3:]

        external_ips = [master.executor.sshclient.addr for master in masters] + external_ips

        self.setup_etcd_certs(masters)
        self.install_etcd_cluster(masters)
        join_line = self.install_kube_masters(masters, external_ips=external_ips, unsafe=unsafe, reset=reset)
        for node in nodes:
            node.virtualization.kubernetes.install_minion(join_line)

        conf_text = masters[0].core.file_read('/etc/kubernetes/kubelet.conf')
        self.doneSet("multihost_install")

        return conf_text, join_line

    def install_dependencies(self, reset=False):
        """
        Use the go get command to get dependencies and install.

        @param reset ,,if True will resintall even if the code has been run before.
        """
        if self.doneCheck("install_dependencies", reset):
            return

        # install requirement for the running kubernetes basics
        self.prefab.system.package.mdupdate(reset=True)
        self.prefab.system.package.install('openssl,mercurial,conntrack,ntp,curl,apt-transport-https')
        # self.prefab.runtimes.golang.install()
        self.prefab.virtualization.docker.install(branch='1.12')

        # required for bridge manipulation in ubuntu
        if self.prefab.core.isUbuntu:
            self.prefab.system.package.install('bridge-utils')

        self.doneSet("install_dependencies")

    def install_base(self, reset=False):
        """
        Builds the kubernetes binaries and Moves them to the appropriate location

        @param reset,, bool will default to false, if ture  will rebuild even if the code has been run before.
        """
        if self.doneCheck("install_base", reset):
            return

        if not self.prefab.core.isUbuntu:
            raise RuntimeError(
                'Only ubuntu systems are supported at the moment.')

        self.install_dependencies()
        script_content = """
        apt-get update && apt-get install -y apt-transport-https
        curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add -
        cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
        deb http://apt.kubernetes.io/ kubernetes-xenial main
        """
        self.prefab.core.run(script_content)
        self.prefab.system.package.mdupdate(reset=True)
        self.prefab.system.package.install('kubelet=1.8.5-00,kubeadm=1.8.5-00,kubectl=1.8.5-00')

        # build
        self.doneSet("install_base")

    def setup_etcd_certs(self, nodes, save=False):
        """
        Generate the  kubernets ssl certificates and etcd certifactes to be use by the cluster.
        it is recommended that this method run on a ceprate node that will be controlling the cluster so that
        the certificates will already be there.

        @param nodes,, list(prefab) list of master node prefab connections
        """
        self.prefab.core.dir_remove('$TMPDIR/k8s')
        self.prefab.core.dir_ensure(
            '$TMPDIR/k8s/crt $TMPDIR/k8s/key $TMPDIR/k8s/csr')
        # get node ips from prefab
        nodes_ip = [node.executor.sshclient.addr for node in nodes]

        # format ssl config to add these node ips and dns names to them
        alt_names_etcd = '\n'.join(['IP.{i} = {ip}'.format(i=i, ip=ip) for i, ip in enumerate(nodes_ip)])
        alt_names_etcd += '\n' + '\n'.join(['DNS.{i} = {hostname}'.format(i=i, hostname=node.core.hostname) for i, node in enumerate(nodes)])
        ssl_config = OPENSSL.format(alt_names_etcd=alt_names_etcd)

        # generate certigicates and sign them for use by etcd
        self.prefab.core.file_write('$TMPDIR/k8s/openssl.cnf', ssl_config)
        cmd = """
        openssl genrsa -out $TMPDIR/k8s/key/etcd-ca.key 4096
        openssl req -x509 -new -sha256 -nodes -key $TMPDIR/k8s/key/etcd-ca.key -days 3650 -out $TMPDIR/k8s/crt/etcd-ca.crt -subj "/CN=etcd-ca" -extensions v3_ca -config $TMPDIR/k8s/openssl.cnf
        openssl genrsa -out $TMPDIR/k8s/key/etcd.key 4096
        openssl req -new -sha256 -key $TMPDIR/k8s/key/etcd.key -subj "/CN=etcd" -out $TMPDIR/k8s/csr/etcd.csr
        openssl x509 -req -in $TMPDIR/k8s/csr/etcd.csr -sha256 -CA $TMPDIR/k8s/crt/etcd-ca.crt -CAkey $TMPDIR/k8s/key/etcd-ca.key -CAcreateserial -out $TMPDIR/k8s/crt/etcd.crt -days 365 -extensions v3_req_etcd -extfile $TMPDIR/k8s/openssl.cnf
        openssl genrsa -out $TMPDIR/k8s/key/etcd-peer.key 4096
        openssl req -new -sha256 -key $TMPDIR/k8s/key/etcd-peer.key -subj "/CN=etcd-peer" -out $TMPDIR/k8s/csr/etcd-peer.csr
        openssl x509 -req -in $TMPDIR/k8s/csr/etcd-peer.csr -sha256 -CA $TMPDIR/k8s/crt/etcd-ca.crt -CAkey $TMPDIR/k8s/key/etcd-ca.key -CAcreateserial -out $TMPDIR/k8s/crt/etcd-peer.crt -days 365 -extensions v3_req_etcd -extfile $TMPDIR/k8s/openssl.cnf
        """
        self.prefab.core.run(cmd)
        if save:
            self.prefab.core.file_copy('$TMPDIR/k8s', '$HOMEDIR/')

    def copy_etcd_certs(self, controller_node):
        """
        Copies the etcd certiftes from $TMPDIR/k8s/ to the controller node to the current node. This assumes certs
        are created in the specified location.

        @param controller_node ,, object(prefab) prefab connection to the controller node which deploys the cluster should have ssh access to all nodes.
        """
        _, user, _ = controller_node.core.run('whoami')
        controller_node.system.ssh.define_host(self.prefab.executor.sshclient.addr, user)
        cmd = """
        scp -P {port} $TMPDIR/k8s/crt/etcd* {node_ip}:{cfg_dir}/etcd/pki/
        scp -P {port} $TMPDIR/k8s/key/etcd* {node_ip}:{cfg_dir}/etcd/pki/
        """.format(node_ip=self.prefab.executor.sshclient.addr, cfg_dir=self.prefab.executor.dir_paths['CFGDIR'],
                   port=self.prefab.executor.sshclient.port or 22)
        if controller_node.executor.type == 'ssh':
            cmd = """
            scp -P {port} {prefab_ip}:$TMPDIR/k8s/crt/etcd* {node_ip}:{cfg_dir}/etcd/pki/
            scp -P {port} {prefab_ip}:$TMPDIR/k8s/key/etcd* {node_ip}:{cfg_dir}/etcd/pki/
            """.format(node_ip=self.prefab.executor.sshclient.addr, cfg_dir=self.prefab.executor.dir_paths['CFGDIR'],
                       port=self.prefab.executor.sshclient.port or 22)

        controller_node.core.execute_bash(cmd)

    def get_etcd_binaries(self, version='3.2.9'):
        """
        Download etcd tar with the specified version extract the binaries place them and the certs in the appropriate location.

        @param version ,, str numbered version of etcd to install.
        """
        etcd_ver = version if version.startswith('v') else 'v%s' % version
        cmd = """
        cd $TMPDIR/etcd_{etcd_ver}
        curl -L {google_url}/{etcd_ver}/etcd-{etcd_ver}-linux-amd64.tar.gz -o etcd-{etcd_ver}-linux-amd64.tar.gz
        tar xzvf etcd-{etcd_ver}-linux-amd64.tar.gz -C .
        """.format(google_url='https://storage.googleapis.com/etcd', etcd_ver=etcd_ver,
                   github_url='https://github.com/coreos/etcd/releases/download')
        self.prefab.core.dir_ensure('$TMPDIR/etcd_{etcd_ver}'.format(etcd_ver=etcd_ver))
        self.prefab.core.run(cmd)
        self.prefab.core.dir_ensure('$BINDIR')
        self.prefab.core.file_copy('$TMPDIR/etcd_{etcd_ver}/etcd-{etcd_ver}-linux-amd64/etcd'.format(etcd_ver=etcd_ver),
                                   '$BINDIR/etcd')
        self.prefab.core.file_copy('$TMPDIR/etcd_{etcd_ver}/etcd-{etcd_ver}-linux-amd64/etcdctl'.format(etcd_ver=etcd_ver),
                                   '$BINDIR/etcdctl')
        self.prefab.core.dir_remove("$CFGDIR/etcd/pki")
        self.prefab.core.dir_remove("/var/lib/etcd")
        self.prefab.core.dir_ensure('$CFGDIR/etcd/pki /var/lib/etcd')

    def install_etcd_cluster(self, nodes):
        """
        This installs etcd binaries and sets up the etcd cluster.

        @param nodes,, list(prefab) list of master node prefabs
        """

        nodes_ip = [node.executor.sshclient.addr for node in nodes]
        initial_cluster = ['%s=https://%s:2380' % (node.core.hostname, node.executor.sshclient.addr) for node in nodes]
        initial_cluster = ','.join(initial_cluster)
        for index, node in enumerate(nodes):
            pm = node.system.processmanager.get('systemd')
            node.virtualization.kubernetes.get_etcd_binaries()
            node.virtualization.kubernetes.copy_etcd_certs(self.prefab)

            etcd_service = ETCD_SERVICE.format(*nodes_ip, name=node.core.hostname, node_ip=node.executor.sshclient.addr,
                                               initial_cluster=initial_cluster)

            node.core.file_write('/etc/systemd/system/etcd.service', etcd_service, replaceInContent=True)
            pm.reload()
            pm.restart('etcd')

    def wait_on_apiserver(self):
        """
        Wait for the api to restart
        """
        timer = 0
        while not self.prefab.system.process.tcpport_check(6443):
            time.sleep(1)
            timer = + 1
            if timer > 30:
                return

    def install_kube_masters(self, nodes, external_ips, kube_cidr='10.0.0.0/16', flannel=True, dashboard=False, unsafe=False, reset=False):
        """
        Used to install kubernetes on master nodes configuring the flannel module and creating the certs
        will also optionally install dashboard

        @param nodes,, list(prefab) list of master node prefabs
        @param kube_cidr,,str Depending on what third-party provider you choose, you might have to set the --pod-network-cidr to something provider-specific.
        @param flannel,,bool  if true install and configure flannel
        @param dashboard,,bool install and configure dashboard(could not expose on OVC)
        @param external_ips,,list(str) list of extra ips to add to certs
        @param unsafe,, bool will allow pods to be created on master nodes.
        """
        if self.doneCheck("install_master", reset):
            return

        if flannel:
            kube_cidr = '10.244.0.0/16'

        for node in nodes:
            node.virtualization.kubernetes.install_base()

        # format docs and command with ips and names
        nodes_ip = [node.executor.sshclient.addr for node in nodes]
        init_node = nodes[0]
        cmd = 'kubeadm init --config %s/kubeadm-init.yaml' % (
            init_node.executor.dir_paths['HOMEDIR'])
        endpoints = ''.join(['  - https://%s:2379\n' % ip for ip in nodes_ip])
        dns_names = [node.core.hostname for node in nodes]
        external_ips = j.data.serializer.yaml.dumps(external_ips + dns_names)
        kube_init_yaml = KUBE_INIT.format(node_ip=nodes_ip[0], flannel_subnet=kube_cidr, endpoints=endpoints,
                                          external_ips=external_ips)

        # write config and run command
        init_node.core.file_write('%s/kubeadm-init.yaml' % init_node.executor.dir_paths['HOMEDIR'],
                                  kube_init_yaml, replaceInContent=True)
        rc, out, err = init_node.core.run(cmd)
        if rc != 0:
            raise RuntimeError(err)
        for line in reversed(out.splitlines()):
            if line.startswith('  kubeadm join --token'):
                join_line = line
                break

        # exchange keys to allow for ssh and scp from the init node to the other
        pub_key = init_node.core.file_read(init_node.system.ssh.keygen()).strip()
        for node in nodes[1:]:
            node.executor.sshclient.ssh_authorize('root', pub_key)
            _, user, _ = init_node.core.run('whoami')
            init_node.system.ssh.define_host(node.executor.sshclient.addr, user)

        if flannel:
            init_node.core.run(
                'kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f https://raw.githubusercontent.com/coreos/flannel/v0.9.0/Documentation/kube-flannel.yml')

        if dashboard:
            init_node.core.run(
                'kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/src/deploy/recommended/kubernetes-dashboard.yaml')

        log_message = """
        please wait until kube-dns deplyments are deployed before joining new nodes to the cluster.
        to check this use 'kubectl get pods --all-namepspaces'
        then pass the join line returned string to the install_minion
        """
        print(log_message)

        # remove node constriction for APISERVER
        pm = init_node.system.processmanager.get('systemd')
        pm.stop('kubelet')
        pm.stop('docker')
        init_node.core.run('sed -i.bak "s/,NodeRestriction//g" /etc/kubernetes/manifests/kube-apiserver.yaml')
        pm.start('kubelet')
        pm.start('docker')

        init_node.virtualization.kubernetes.wait_on_apiserver()

        edit_cmd = """
        cd /etc/kubernetes
        sed -i.bak "s/kub01/{my_hostname}/g" /etc/kubernetes/*.conf
        sed -i.bak "s/{init_ip}/{node_ip}/g" /etc/kubernetes/*.conf
        sed -i.bak "s/advertise-address={init_ip}/advertise-address={node_ip}/g" /etc/kubernetes/manifests/kube-apiserver.yaml
        """
        send_cmd = """
        eval `ssh-agent -s`
        ssh-add /root/.ssh/default
        rsync -av -e ssh --progress /etc/kubernetes {master}:/etc/
        """
        node_json = {
            "metadata": {
                "labels": {
                    "node-role.kubernetes.io/master": ""
                }
            },
            "spec": {
                "taints": [{
                    "effect": "NoSchedule",
                    "key": "node-role.kubernetes.io/master",
                    "timeAdded": None
                }]
            }
        }

        if unsafe:
            # if unsafe  comppletly remove role master from the cluster
            init_node.core.run(
                'kubectl --kubeconfig=/etc/kubernetes/admin.conf taint nodes %s node-role.kubernetes.io/master-' % init_node.core.hostname)
        else:
            # write patch file used later on to register the nodes as masters
            init_node.core.file_write('/master.yaml', j.data.serializer.yaml.dumps(node_json))

        for index, master in enumerate(nodes[1:]):
            # send certs from init node to the rest of the master nodes
            init_node.core.execute_bash(send_cmd.format(master=master.executor.sshclient.addr))
            # adjust the configs in the new nodes with the relative ip and hostname
            master.core.execute_bash(edit_cmd.format(node_ip=master.executor.sshclient.addr,
                                                     my_hostname=init_node.core.hostname,
                                                     init_ip=init_node.executor.sshclient.addr))

            pm = master.system.processmanager.get('systemd')
            pm.reload()
            pm.restart('kubelet')
            pm.restart('docker')
            master.virtualization.kubernetes.wait_on_apiserver()

            # giving time for the nodes to be registered
            for i in range(30):
                _, nodes_result, _ = init_node.core.run('kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes',
                                                        showout=False)
                # checking if number of lines is equal to number of nodes to check if they are registered
                if len(nodes_result.splitlines()) - 1 == index + 2:
                    break

            if not unsafe:
                # else setting the nodes as master
                register_cmd = """kubectl --kubeconfig=/etc/kubernetes/admin.conf patch node %s -p "$(cat /master.yaml)"
                """ % (master.core.hostname)
                init_node.core.execute_bash(register_cmd)

        # build
        self.doneSet("install_master")

        return join_line

    def install_minion(self, join_line, reset=False):
        """
        Used to install the basic componenets of kubernetes on a minion node and make that node join the cluster
        specified in the join line param.

        @param join_line ,,str an output line produced when deploying a master node this is the return from install_master method.
        @param reset ,,bool bool will default to false, if ture  will rebuild even if the code has been run before.
        """
        if self.doneCheck("install_minion", reset):
            return

        self.install_base()
        self.prefab.core.run(join_line.strip())

        # build
        self.doneSet("install_minion")

    def generate_new_token(self, nodes):
        """
        TODO
        """
        pass
