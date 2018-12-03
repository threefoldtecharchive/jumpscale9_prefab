"""
This script will create an flist that contains the required services to run the
Jumpscale Descentralized Exchange
"""

from jumpscale import j
from time import sleep
from jose.jwt import get_unverified_claims
import json
import os

DEFAULT_ELECTRUM_VERSION = '3.2.2'
ELECTRUM_FLIST_NAME = 'electrum.flist'
JS9_DEX_FLIST_NAME = 'js9_dex.flist'

iyo_client = j.clients.itsyouonline.get()
claims = get_unverified_claims(iyo_client.jwt)
username = claims.get("username", None)


def main(prefab):
    # install electrum wallet
    prefab.blockchain.electrum.install(tag=os.environ.get('ELECTRUM_VERSION', DEFAULT_ELECTRUM_VERSION))
    data_dir = j.sal.fs.getTmpDirPath()
    electrum_bin_path = j.sal.fs.joinPaths(j.dirs.BINDIR, 'electrum')
    j.tools.sandboxer.sandbox_chroot(electrum_bin_path, data_dir)

    # create the flist
    electrum_archive_file = '/tmp/{}.tar.gz'.format(ELECTRUM_FLIST_NAME)
    prefab.core.execute_bash('cd {} && tar -czf {} .'.format(data_dir, electrum_archive_file))

    zhub_data = {'token_': iyo_client.jwt_get(), 'username': username,'url': 'https://hub.gig.tech/api'}
    zhub_client = j.clients.zhub.get(instance="main", data=zhub_data)
    if hasattr(zhub_client, 'authentificate'):
        zhub_client.authentificate()
    else:
        zhub_client.authenticate()

    zhub_client.upload(electrum_archive_file)

    # merge the electrum flist with a base ubuntu flist and the jumpscale flist
    sources = ['gig-official-apps/ubuntu1604-for-js.flist',
                'abdelrahman_hussein_1/js9_sandbox.flist',
                'abdelrahman_hussein_1/ubuntu_xenial_boot.flist',
                '{}/{}'.format(zhub_client.config.data['username'], ELECTRUM_FLIST_NAME)]
    url = '{}/flist/me/merge/{}'.format(zhub_client.api.base_url, JS9_DEX_FLIST_NAME)
    resp = zhub_client.api.post(uri=url, data=json.dumps(sources), headers=None, params=None, content_type='application/json')
    if resp.status_code != 200:
        raise RuntimeError('Failed to merge sources {}. Error: {}'.format(sources, resp.text))

    print("Done! New flist can be found under: {}".format('{}/{}'.format(zhub_client.config.data['username'], JS9_DEX_FLIST_NAME)))


if __name__ == '__main__':
    prefab = j.tools.prefab.local
    main(prefab)
