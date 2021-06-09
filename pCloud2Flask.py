from flask import Flask, request, redirect
import json
import random
import requests
import threading
import urllib.parse

import logging
logger = logging.getLogger('BatHome')

PLACEHOLDER_IMG_URL = "https://upload.wikimedia.org/wikipedia/en/e/ed/Nyan_cat_250px_frame.PNG"

class pCloudAuth(object):
    def __init__(self, client_id, client_secret, cache_fname):
        self.client_id, self.client_secret, self.cache_fname = client_id, client_secret, cache_fname
        self.tok = None

        try:
            import json
            with open(self.cache_fname, 'r') as fp:
                cache = json.loads(fp.read())
                self.tok = cache['tok']
        except FileNotFoundError:
            pass
        except:
            logger.warning("pCloud: Couldn't read auth tok cache from {}".format(self.cache_fname), exc_info=True)

    def is_valid(self):
        return self.tok != None

    def get_auth_step1(self):
        return 'https://my.pcloud.com/oauth2/authorize?client_id={}&response_type=code'.\
                                format(self.client_id)

    def get_auth_step2(self, code):
        url = 'https://api.pcloud.com/oauth2_token?client_id={}&client_secret={}&code={}' \
                                .format(self.client_id, self.client_secret, code)
        r = requests.get(url)
        self.tok = r.json()['access_token']

        try:
            with open(self.cache_fname, 'w+') as fp:
                fp.write(json.dumps({'tok': self.tok}))
        except:
            logger.error("pCloudAuth couldn't write auth tok cache to {}".format(self.cache_fname), exc_info=True)

        return self.tok

    def build_url(self, method, args):
        return 'https://api.pcloud.com/{}?access_token={}&{}'.format(method, self.tok,
                                                                 urllib.parse.urlencode(args))


class pCloudWgetImg(object):
    def __init__(self, auth, cache_fname, src_paths, ext_filter):
        self.auth = auth

        self.cache_fname = cache_fname
        self.cached_pics_list = []
        self.src_paths = src_paths

        self.ext_filter = set([x.lower() for x in ext_filter])
        self._bg_thread = None
        self.refresh_cached_file_list()

    def _has_accepted_extension(self, filepath):
        p = filepath.lower()
        for ext in self.ext_filter:
            if p.endswith(ext):
                return True
        return False

    def _recursive_ls(self, cloud_path):
        logger.info("pCloud: cloud ls " + cloud_path)
        r = requests.get(self.auth.build_url('listfolder', {'path': cloud_path}))
        if 'error' in r.json() and r.json()['result'] == 2005:
            raise KeyError("No remote directory {}".format(cloud_path))

        lst = []
        for cloud_file in r.json()['metadata']['contents']:
            if not cloud_file['isfolder']:
                if self._has_accepted_extension(cloud_file['path']):
                    lst.append(cloud_file['path'])
            else:
                lst.extend(self._recursive_ls(cloud_file['path']))

        return lst

    def _bg_refresh_cached_file_list(self):
        disk_cache = {}
        try:
            import json
            with open(self.cache_fname, 'r') as fp:
                disk_cache = json.loads(fp.read())
        except FileNotFoundError:
            pass
        except:
            logger.warning("pCloudSlideshow: Couldn't read cache from {}".format(self.cache_fname), exc_info=True)

        self.cached_pics_list = []
        new_disk_cache = {}
        for path in self.src_paths:
            logger.info("Updating pCloudSlideshow pictures from {}. Might take a while...".format(path))

            if path in disk_cache.keys():
                new_disk_cache[path] = disk_cache[path]
            else:
                new_disk_cache[path] = self._recursive_ls(path)
                logger.info(f"pCloud path read from cloud: {path}")

            self.cached_pics_list.extend(new_disk_cache[path])

        logger.info("pCloudSlideshow finished updating, found {} files. Caching paths.".\
                        format(len(self.cached_pics_list)))

        try:
            with open(self.cache_fname, 'w+') as fp:
                fp.write(json.dumps(new_disk_cache))
        except:
            logger.error("pCloudSlideshow couldn't write cache to {}".format(self.cache_fname), exc_info=True)

    def force_refresh_cached_file_list(self):
        try:
            with open(self.cache_fname, 'w+') as fp:
                fp.write('')
        except:
            pass
        self.refresh_cached_file_list()

    def refresh_cached_file_list(self):
        if self._bg_thread is not None:
            self._bg_thread.join()

        logger.info("Refreshing pCloud paths cache in a background thread. This is a slow op")
        self._bg_thread = threading.Thread(target=self._bg_refresh_cached_file_list)
        self._bg_thread.start()

    def _get_file_url(self, cloudpath):
        r = requests.get(self.auth.build_url('getfilelink', {'path': cloudpath})).json()
        try:
            url = 'https://' + random.choice(r['hosts']) + r['path']
            return url
        except KeyError as ex:
            logger.error("pCloud sent reply I can't understand: {}".format(str(r.text)))
            raise ex

    def _get_random_img_url(self):
        if len(self.cached_pics_list) == 0:
            self.refresh_cached_file_list()
            return PLACEHOLDER_IMG_URL
        return self._get_file_url(random.choice(self.cached_pics_list))

    def get_random_img_url(self):
        try:
            return self._get_random_img_url()
        except:
            logger.error("pCloud slideshow exception while getting image url. Probably no auth.", exc_info=True)
            return PLACEHOLDER_IMG_URL

    def has_valid_auth(self):
        try:
            return self._get_random_img_url() != None
        except:
            return False


PCLOUD_AUTH_STEP1_TMPL = """
<form action='/pcloud/auth_step2'>
<ol>
  <li>Goto <a href='{}' target='_blank'> this link to request pCloud-authentication</a>
  <li>Login to pCloud
  <li>Paste the access code here: <input name='access_code'/>
  <li><input type='submit' value='Submit'/>
</ol>
</form>
"""

def build_pcloud_and_register_to_flask(flask, flask_api_url_prefix, cfg):
    auth = pCloudAuth(cfg['client_id'], cfg['client_secret'], cfg['auth_cache_file'])
    pcloud_cli = pCloudWgetImg(auth, cfg['paths_cache'], cfg['interesting_paths'], cfg['accepted_extensions'])

    @flask.route(flask_api_url_prefix)
    @flask.route(flask_api_url_prefix+ '/get_random_image_url')
    def pcloud_idx():
        return pcloud_cli.get_random_img_url()

    @flask.route(flask_api_url_prefix+ '/see_random_image')
    def pcloud_rnd_img():
        return f"<img src='{pcloud_cli.get_random_img_url()}'/>"

    @flask.route(flask_api_url_prefix+ '/goto_random_image')
    def pcloud_goto_rnd_img():
        return redirect(pcloud_cli.get_random_img_url(), code=302)

    @flask.route(flask_api_url_prefix + '/refresh_url_cache')
    def pcloud_refresh_url_cache():
        pcloud_cli.force_refresh_cached_file_list()
        return "Refresh scheduled (this is a slow OP!)"

    @flask.route(flask_api_url_prefix + '/is_auth')
    def pcloud_is_auth():
        return json.dumps({'valid_auth': pcloud_cli.has_valid_auth()})

    @flask.route(flask_api_url_prefix + '/auth')
    def pcloud_reauth_step1():
        return PCLOUD_AUTH_STEP1_TMPL.format(auth.get_auth_step1())

    @flask.route(flask_api_url_prefix + '/auth_step2')
    def pcloud_reauth_step2():
        code = request.args.get("access_code")
        tok = auth.get_auth_step2(code)
        if tok:
            return f"Code is valid! <a href='{flask_api_url_prefix}'>Continue</a>"
        else:
            return f"Code not valid. <a href='{flask_api_url_prefix}/auth'>Try again</a>."

    return pcloud_cli


