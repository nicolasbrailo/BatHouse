import urllib.parse
import requests
import random
import json
from apscheduler.schedulers.background import BackgroundScheduler

import logging
logger = logging.getLogger('BatHome')

class pCloudAuth(object):
    def __init__(self, client_id, client_secret, cache_fname):
        self.client_id, self.client_secret, self.cache_fname = client_id, client_secret, cache_fname
        self.tok = None

        try:
            import json
            with open(self.cache_fname, 'r') as fp:
                cache = json.loads(fp.read())
                self.tok = cache['tok']
        except:
            logger.warning("pCloud: Couldn't read auth tok cache from {}".format(self.cache_fname), exc_info=True)

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


    def _has_accepted_extension(self, filepath):
        p = filepath.lower()
        for ext in self.ext_filter:
            if p.endswith(ext):
                return True
        return False


    def _recursive_ls(self, cloud_path):
        r = requests.get(self.auth.build_url('listfolder', {'path': cloud_path}))
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


    def refresh_cached_file_list(self):
        try:
            import json
            with open(self.cache_fname, 'r') as fp:
                disk_cache = json.loads(fp.read())
        except:
            logger.warning("pCloudSlideshow: Couldn't read cache from {}".format(self.cache_fname), exc_info=True)
            disk_cache = {}

        self.cached_pics_list = []
        new_disk_cache = {}
        for path in self.src_paths:
            logger.info("Updating pCloudSlideshow pictures from {}. Might take a while...".format(path))

            if path in disk_cache.keys():
                new_disk_cache[path] = disk_cache[path]
                logger.debug("pCloudSlideshow read from cache")
            else:
                new_disk_cache[path] = self._recursive_ls(path)
                logger.debug("pCloudSlideshow read from cloud")

            self.cached_pics_list.extend(new_disk_cache[path])

        logger.info("pCloudSlideshow finished updating, found {} files. Caching paths.".\
                        format(len(self.cached_pics_list)))

        try:
            with open(self.cache_fname, 'w+') as fp:
                fp.write(json.dumps(new_disk_cache))
        except:
            logger.error("pCloudSlideshow couldn't write cache to {}".format(self.cache_fname), exc_info=True)


    def _get_file_url(self, cloudpath):
        r = requests.get(self.auth.build_url('getfilelink', {'path': cloudpath})).json()
        url = 'https://' + random.choice(r['hosts']) + r['path']
        return url

    def get_random_img_url(self):
        try:
            if len(self.cached_pics_list) == 0:
                self.refresh_cached_file_list()
            return self._get_file_url(random.choice(self.cached_pics_list))
        except:
            logger.error("pCloud slideshow exception while getting image url. Probably no auth.", exc_info=True)
            return "https://upload.wikimedia.org/wikipedia/en/e/ed/Nyan_cat_250px_frame.PNG"


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
                self.callback_another_cast_started()

    def __init__(self, update_time_secs, img_provider, chromecast):
        self.update_time_secs, self.img_provider, self.chromecast = \
                update_time_secs, img_provider, chromecast

        self.scheduler = BackgroundScheduler()
        self.sched_job_obj = None
        chromecast.register_status_listener(pCloudCastSlideshow.CC_Listener(self._on_someone_else_casting))
        self.scheduler.start()

    def start(self):
        if self.sched_job_obj is None:
            logger.debug("Start pCloudCastSlideshow")
            # Force a fist image update; otherwise the scheduler will only
            # trigger the job after the first interval
            self.show_image()
            self.sched_job_obj = self.scheduler.add_job(func=self.show_image,
                                   trigger="interval", seconds=self.update_time_secs)

    def _on_someone_else_casting(self):
        if self.sched_job_obj is not None:
            logger.info("Someone started casting: stop pCloud slideshow")
            self.stop()

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


def build_pcloud_slideshow_from_cfg(CFG, chromecast, flask_app):
    auth = pCloudAuth(CFG['pcloud_client_id'], CFG['pcloud_client_secret'], CFG['pcloud_auth_cache_file'])
    img_provider = pCloudWgetImg(auth, CFG["pcloud_slideshow_cache_file"],
                                       CFG["pcloud_slideshow_src_paths"],
                                       CFG["pcloud_slideshow_extensions_filter"])
    slideshow = pCloudCastSlideshow(int(CFG['pcloud_slideshow_update_image_secs']), img_provider, chromecast)

    @flask_app.route('/pcloud_slideshow/auth/step1')
    def flask_ep_pcloud_slideshow_auth_step1():
        return "<a href='{}'>Auth pCloud</a>".format(slideshow.img_provider.auth.get_auth_step1())

    @flask_app.route('/pcloud_slideshow/auth/step2/<code>')
    def flask_ep_pcloud_slideshow_auth_step2(code):
        return slideshow.img_provider.auth.get_auth_step2(code)

    @flask_app.route('/pcloud_slideshow/images/refresh_cache')
    def flask_ep_pcloud_slideshow_images_refresh_cache():
        slideshow.img_provider.refresh_cached_file_list()
        return "OK"

    @flask_app.route('/pcloud_slideshow/images/random')
    def flask_ep_pcloud_slideshow_images_random():
        return slideshow.img_provider.get_random_img_url()

    @flask_app.route('/pcloud_slideshow/start')
    def flask_ep_pcloud_slideshow_start():
        slideshow.start()
        return "OK"

    @flask_app.route('/pcloud_slideshow/stop')
    def flask_ep_pcloud_slideshow_stop():
        slideshow.stop()
        return "OK"

    return slideshow

