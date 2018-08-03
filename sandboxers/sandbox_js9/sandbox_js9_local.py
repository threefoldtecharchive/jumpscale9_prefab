from jumpscale import j
import json

j.logger.loggers_level_set(20)
iyo_client = j.clients.itsyouonline.get()
prefab = j.tools.prefab.local

def build(prefab):
    """
    Build sandboxed js9
    """
    prefab.core.run("js_shell 'j.tools.sandboxer.python.do(reset=True)'", timeout=1800)


def upload(prefab):
    """
    Uploaded the generated flist, merge it with a base ubuntu image and upload the new full flist
    """
    prefab.core.execute_bash('''curl -b 'caddyoauth=%s' -F file=@/opt/var/build/sandbox/js9_sandbox.tar.gz https://hub.gig.tech/api/flist/me/upload''' % (iyo_client.jwt))
    # zhub_data = {'token_': iyo_client.jwt, 'username': 'abdelrahman_hussein_1','url': 'https://hub.gig.tech/api'}
    # zhub_client = j.clients.zerohub.get(data=zhub_data)
    zhub_client = j.clients.zhub.get()
    zhub_client.authenticate()
    sources = ['gig-official-apps/ubuntu1604-for-js.flist',
                'abdelrahman_hussein_1/capacity_checker_js9.flist',
                '{}/js9_sandbox.flist'.format(zhub_client.config.data['username'])]
    target = 'js9_sandbox_full.flist'
    url = '{}/flist/me/merge/{}'.format(zhub_client.api.base_url, target)
    resp = zhub_client.api.post(uri=url, data=json.dumps(sources), headers=None, params=None, content_type='application/json')


def start(prefab):
    build(prefab)
    upload(prefab)

start(prefab)
