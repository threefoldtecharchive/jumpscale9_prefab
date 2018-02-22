from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabCoreDns(app):
    NAME = "coredns"

    def _init(self):
        self.GOPATHDIR = self.prefab.core.dir_paths['BASEDIR'] + "/go_proj"

    def install(self, domain, reset=False):
        """
        installs and runs coredns server with redis plugin
        """

        if self.doneCheck("install", reset):
            return
        # install golang
        self.prefab.runtimes.golang.install()

        # install redis
        self.prefab.db.redis.install()
        self.prefab.db.redis.start(ip='0.0.0.0')

        # install coredns
        self.prefab.core.run('go get github.com/coredns/coredns', die=False)
        coredns_dir = self.GOPATHDIR + '/src/github.com/coredns/coredns'
        plugins_path = coredns_dir + '/plugin.cfg'
        self.prefab.core.file_write(plugins_path, self.coredns_plugins)
        # configure coredns
        config = """
. {
    redis %s {
        address localhost:6379
        connect_timeout 100
        read_timeout 100
        ttl 360
        prefix _dns:
    }
}
        """ % domain
        config_path = self.prefab.core.dir_paths['CFGDIR'] + "/Corefile"
        self.prefab.core.file_write(config_path, config)
        # install coredns redis plugin
        cmd = """
        go get github.com/arvancloud/redis
        cd {coredns_dir}
        go generate
        go build
        """.format(coredns_dir=coredns_dir)

        # start coredns 
        self.start(coredns_dir + "/coredns", config_path)
        
        self.doneSet('install')


    def start(self, coredns_path, config_path):
        
        cmd = "{coredns_path} -conf {config_path}".format(coredns_path=coredns_path, config_path=config_path)
        self.prefab.system.processmanager.get().ensure("coredns", cmd, wait=10, expect='53')

    def register_a_record(self, ns_addr, domain_name, subdomain, resolve_to=None, redis_port=6379, redis_password='', ttl=300, override=False):
        """registers an A record on a coredns server through redis connection
        
        Arguments:
            ns_addr {string} -- dns ip address
            domain_name {string} -- domain to register an A record on
            subdomain {string} -- subdomain to regsiter
        
        Keyword Arguments:
            resolve_to {string} -- target ip, if none will use the machine pub ip (default: {None})
            redis_port {number} -- redis port allowed by the dns server (default: {6379})
            redis_password {string} -- redis password (default: {None})
            ttl {number} -- time to live (default: 300)
            override {boolean} -- if true it will override if A record exists (default: {False})
        """

        self.prefab.system.package.install("redis-tools")
        if redis_password:
            redis_password = '-a {}'.format(redis_password)
        
        if redis_port:
            redis_port = '-p {}'.format(redis_port)

        if ns_addr:
            ns_addr = '-h {}'.format(ns_addr)

        command = 'HGET {domain_name} {subdomain}'
        # check connection and check if key exists
        rc, out, _ = self.prefab.core.run('redis-cli {ns_addr} {redis_port} {redis_password} {command}'.format(
                         ns_addr=ns_addr, redis_port=redis_port, redis_password=redis_password, command=command))
        if rc != 0:
            raise RuntimeError("Can't connect to {ns_addr} on port {port},"
                               "please make sure that this host is reachable and redis server is running")
        exist = False
        if out:
            exist = True

        if not exist or override:
            a_record = "{\"a\":[{\"ttl\":300, \"ip\":\"%s\"}]}" % resolve_to
            
            command = 'HSET {domain_name} {subdomain} "{a_record}"'.format(domain_name=domain_name, subdomain=subdomain,
                                                                         a_record=a_record)

            rc, out, _ = self.prefab.core.run('redis-cli {ns_addr} {redis_port} {redis_password} {command}'.format(
                         ns_addr=ns_addr, redis_port=redis_port, redis_password=redis_password, command=command))
        
        from IPython import embed
        embed(colors='Linux')

    @property
    def coredns_config(self):
        return """
        
        """


    @property
    def coredns_plugins(self):
        plugins = """
tls:tls
nsid:nsid
root:root
bind:bind
debug:debug
trace:trace
health:health
pprof:pprof
prometheus:metrics
errors:errors
log:log
dnstap:dnstap
chaos:chaos
loadbalance:loadbalance
cache:cache
rewrite:rewrite
dnssec:dnssec
autopath:autopath
reverse:reverse
template:template
hosts:hosts
route53:route53
federation:federation
kubernetes:kubernetes
file:file
auto:auto
secondary:secondary
etcd:etcd
redis:github.com/arvancloud/redis
forward:forward
proxy:proxy
erratic:erratic
whoami:whoami
on:github.com/mholt/caddy/onevent
        """
        return plugins