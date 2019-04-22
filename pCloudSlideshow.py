import urllib.parse
import requests
import random
from apscheduler.schedulers.background import BackgroundScheduler

import logging
logger = logging.getLogger('BatHome')

class pCloudAuth(object):
    def __init__(self, client_id, client_secret, tok=None):
        self.client_id, self.client_secret, self.tok = client_id, client_secret, tok

    def get_auth_step1_url(self):
        return 'https://my.pcloud.com/oauth2/authorize?client_id={}&response_type=code'.\
                                format(self.client_id)

    def get_auth_step2(self, code):
        url = 'https://api.pcloud.com/oauth2_token?client_id={}&client_secret={}&code={}' \
                                .format(self.client_id, self.client_secret, code)
        r = requests.get(url)
        self.tok = r.json()['access_token']
        return self.tok

    def get_tok(self):
        return self.tok


class pCloudWgetImg(object):
    def __init__(self, auth, base_path, ext_filter=['jpg', 'jpeg', 'png']):
        self.cached_pics_list = None
        self._auth = auth
        self.base_path = base_path
        self.ext_filter = set([x.lower() for x in ext_filter])

    def _build_url(self, method, args):
        return 'https://api.pcloud.com/{}?access_token={}&{}'.format(method, self._auth.get_tok(),
                                                                 urllib.parse.urlencode(args))

    def _has_accepted_extension(self, filepath):
        p = filepath.lower()
        for ext in self.ext_filter:
            if p.endswith(ext):
                return True
        return False

    def _recursive_ls(self, cloud_path):
        r = requests.get(self._build_url('listfolder', {'path': cloud_path}))
        if 'error' in r.json() and r.json()['result'] == 2005:
            raise KeyError("No remote directory {}".format(cloudpath))

        lst = []
        for cloud_file in r.json()['metadata']['contents']:
            if not cloud_file['isfolder']:
                if self._has_accepted_extension(cloud_file['path']):
                    lst.append(cloud_file['path'])
            else:
                lst.extend(self._recursive_ls(cloud_file['path']))

        return lst

    def _get_file_url(self, cloudpath):
        r = requests.get(self._build_url('getfilelink', {'path': cloudpath})).json()
        url = 'https://' + random.choice(r['hosts']) + r['path']
        return url

    def _get_random_img_path(self):
        if self.cached_pics_list is None:
            self.refresh_cached_file_list()

        return random.choice(self.cached_pics_list)

    def refresh_cached_file_list(self):
        logger.info("Updating list of pictures, might take a while...")
        self.cached_pics_list = self._recursive_ls(self.base_path)
        logger.info("Finished updating list of pictures, found {} files".\
                        format(len(self.cached_pics_list)))

    def get_random_img_url(self):
        return self._get_file_url(self._get_random_img_path())


class pCloudCastSlideshow(object):
    class CC_Listener(object):
        def __init__(self, callback_another_cast_started):
            self.callback_another_cast_started = callback_another_cast_started

        def new_media_status(self, status):
            # Sometimes empty status appear. Should be safe to ignore since if
            # content == null then no one must be casting. I hope.
            if status is None or status.content_id is None:
                return

            # Detect if someone else is casting. If url of content has pcloud, we're safe
            if status.content_id.find('pcloud') == -1:
                logger.debug("New cast detected: {}".format(status.content_id))
                logger.info("Someone started casting: stop pCloud slideshow (if started)")
                self.callback_another_cast_started()

    def __init__(self, update_time_secs, img_provider, chromecast):
        self.update_time_secs, self.img_provider, self.chromecast = \
                update_time_secs, img_provider, chromecast

        self.scheduler = BackgroundScheduler()
        self.sched_job_obj = None
        chromecast.register_status_listener(pCloudCastSlideshow.CC_Listener(self.stop))
        self.scheduler.start()

    def start(self):
        if self.sched_job_obj is None:
            logger.debug("Start pCloudCastSlideshow")
            # Force a fist image update; otherwise the scheduler will only
            # trigger the job after the first interval
            self.show_image()
            self.sched_job_obj = self.scheduler.add_job(func=self.show_image,
                                   trigger="interval", seconds=self.update_time_secs)

    def stop(self):
        if self.sched_job_obj is not None:
            logger.debug("Stop pCloudCastSlideshow")
            self.sched_job_obj.remove()
            self.sched_job_obj = None

    def show_image(self):
        url = self.img_provider.get_random_img_url()
        logger.debug("Asking {} to show image {}".format(self.chromecast.get_id(), url))
        self.chromecast.show_image(url)

    def shutdown(self):
        logger.debug("Shutdown pCloudCastSlideshow")
        self.scheduler.shutdown()

def build_pcloud_slideshow_from_cfg(CFG, chromecast):
    auth = pCloudAuth(CFG['pcloud_client_id'], CFG['pcloud_client_secret'], CFG['pcloud_auth_tok'])
    img_provider = pCloudWgetImg(auth, CFG['pcloud_img_wget_base_path'])
    slideshow = pCloudCastSlideshow(int(CFG['pcloud_img_cast_update_secs']), img_provider, chromecast)
    return slideshow

def set_pcloud_slideshow_flask_bindings(slideshow, flask_app):
    @flask_app.route('/pcloud/auth/step1')
    def flask_ep_pcloud_auth_step1():
        return "<a href='{}'>Auth pCloud</a>".format(slideshow.img_provider._auth.get_auth_step1_url())

    @flask_app.route('/pcloud/auth/step2/<code>')
    def flask_ep_pcloud_auth_step2(code):
        return slideshow.img_provider._auth.get_auth_step2_url(code)

    @flask_app.route('/pcloud/update cache list')
    def adasd():
        return "OK"

    @flask_app.route('/pcloud/stop')
    def flask_ep_pcloud_stop():
        slideshow.stop()
        return "OK"

    @flask_app.route('/pcloud/start')
    def flask_ep_pcloud_start():
        slideshow.start()
        return "OK"

