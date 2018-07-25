import urllib3
from js9 import j


base = j.tools.prefab._getBaseClass()


class PrefabCapacity(base):

    def _capacity_start(self):
        """
        create the flist that containts the /etc/start script
        of the zbundle

        [description]

        :return: url of the flist
        :rtype: str
        """
        self.logger.info("create capacity_registation flist")
        path = j.sal.fs.joinPaths(j.sal.fs.getParent(__file__), 'capacity', 'flist')
        tarfile = '/tmp/capacity_registation.tar.gz'
        self.prefab.core.run('tar czf {} -C {} .'.format(tarfile, path))

        hub = _get_hub_client()
        hub.authenticate()
        with open(tarfile, 'rb') as f:
            resp = hub.upload(tarfile)
            resp.raise_for_status()

        flist = '{user}/{flist}'.format(user=hub.config.data['username'], flist=resp.json()['payload']['name'])

        return flist

    def zbundle_build(self):
        self.logger.info("create zbundle_capacity flist")
        capacity_flist = self._capacity_start()
        to_merge = [
            'gig-bootable/ubuntu:16.04.flist',
            'abdelrahman_hussein_1/capacity_checker_js9.flist',
            'zaibon/js9_sandbox.flist',
            capacity_flist,
        ]

        self.logger.info("merging \n%s together..." % ',\n'.join(to_merge))

        hub = _get_hub_client()
        hub.authenticate()

        resp = hub.merge('zbundle_capacity', to_merge)
        if resp.get('status') == 'error':
            raise RuntimeError('fail to merge flists: %s' % resp['message'])

        flist = '{user}/zbundle_capacity.flist'.format(user=hub.config.data['username'])
        hub.api.set_user('gig-official-apps')
        hub.promote(hub.config.data['username'], 'zbundle_capacity', 'zbundle_capacity')

        return "https://hub.gig.tech/gig-official-apps/zbundle_capacity.flist.md"


def _get_hub_client():
    hub = j.clients.zhub.get()
    token = hub.config.data['token_']
    token = j.clients.itsyouonline.refresh_jwt_token(token)
    hub.config.data_set('token_', token)
    hub.config.save()
    return j.clients.zhub.get()
