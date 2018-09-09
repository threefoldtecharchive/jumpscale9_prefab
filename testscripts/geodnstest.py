from Jumpscale import j
import dns.resolver
import time


def test(geodns_install=False, dnsresolver_install=True, port=3333, tmux=True):
    # start geodns instance(this is the main object to be used it is an
    # abstraction of the domain object)
    prefab = j.tools.prefab.local
    geodns = prefab.apps.geodns

    if dnsresolver_install:
        prefab.core.run('pip install dnspython')
        # prefab.core.file_download("http://www.dnspython.org/kits3/1.12.0/dnspython3-1.12.0.tar.gz",
        #                            to="$TMPDIR", overwrite=False, expand=True)
        # tarpath = prefab.core.find("$TMPDIR", recursive=True, pattern="*dns*.gz", type='f')[0]
        # extracted = prefab.core.file_expand(tarpath, "$TMPDIR")
        # prefab.core.run("cd %s && python setup.py" % extracted)

    if geodns_install:
        geodns.install(reset=True)
    geodns.start(port=port, tmux=tmux)

    # create a domain(the domain object is used as for specific trasactions
    # and is exposed for debugging purposes)
    domain_manager = j.clients.domainmanager.get(prefab)
    domain = domain_manager.ensure_domain("gig.com", serial=3, ttl=600)
    self.logger.info(domain._a_records)
    self.logger.info(domain._cname_records)

    # add an A record
    domain.add_a_record("123.45.123.1", "www")
    domain.save()
    # test_connection
    my_resolver = dns.resolver.Resolver()
    my_resolver.nameservers = ['127.0.0.1', '192.168.122.250']
    my_resolver.port = port
    answer1 = my_resolver.query('www.gig.com')
    time.sleep(5)
    if 1 == answer1.rrset[0].rdtype and "123.45.123.1" == answer1.rrset[0].to_text():
        self.logger.info("add A record Test SUCCESS")
    else:
        self.logger.info("failure")

    # add cname record
    domain.add_cname_record("www", "grid")
    domain.save()
    # test connection
    answer2 = my_resolver.query("grid.gig.com", rdtype="cname")
    time.sleep(5)
    if 5 == answer2.rrset[0].rdtype and "www.gig.com." == answer2.rrset[0].to_text():
        self.logger.info("add CNAME record Test SUCCESS")
    else:
        self.logger.info("failure")
    self.logger.info(str(type(answer1)) + str(type(answer2)))

    # get A record
    a_records = domain.get_a_record()

    if a_records == {"www": [["123.45.123.1", 100]]}:
        self.logger.info("get A record Test SUCCESS")

    # get cname record
    cname_records = domain.get_cname_record()
    if cname_records == {"grid": "www"}:
        self.logger.info("get cname cname_records")

    # delete A record
    domain.del_a_record("www", full=True)
    domain.save()
    # test deltion
    try:
        answer1 = my_resolver.query('www.gig.com')
    except Exception as e:
        self.logger.info(str(e))

    # delete cname record
    domain.del_cname_record("grid")
    domain.save()
    # test deltion
    try:
        answer1 = my_resolver.query('grid.gig.com')
    except Exception as e:
        self.logger.info(str(e))


if __name__ == "__main__":
    test(geodns_install=False)
