import time

import logging
logger = logging.getLogger('BatHome')

from apscheduler.schedulers.background import BackgroundScheduler

class ChromecastSlideshow():
    def __init__(self, world, cc_name, img_uri_provider):
        self.world = world
        self.cc_name = cc_name
        self.cc = None
        self.img_uri_provider = img_uri_provider

    def _try_connect(base_func):
        def wrap(self, *a, **kw):
            if self.cc is None:
                self.cc = self.world.get_thing_by_name(self.cc_name)

            if self.cc is None:
                logger.warning("Ignoring {str(self.base_func} for {self.cc_name}: not connected")
            else:
                return base_func(self, *a, **kw)

        return wrap

    @_try_connect
    def show_image(self):
        url = self.img_uri_provider.get_random_img_url() + "?nocache=" + str(time.time())
        logger.debug("Asking {} to show image {}".format(self.cc_name, url))
        self.cc.show_image(url)
        return url



def build_slideshow_and_register_to_flask(flask, flask_api_url_prefix, img_uri_provider, world, cc_name):
    cs = ChromecastSlideshow(world, cc_name, img_uri_provider)

    @flask.route(flask_api_url_prefix)
    @flask.route(flask_api_url_prefix + '/show_image')
    def idx():
        url = cs.show_image()
        return "Showing " + url

#
#
#class pCloudCastSlideshow(object):
#    class CC_Listener(object):
#        def __init__(self, callback_another_cast_started):
#            self.callback_another_cast_started = callback_another_cast_started
#
#        def new_media_status(self, status):
#            # Sometimes empty status appear. Should be safe to ignore since if
#            # content == null then no one must be casting. I hope.
#            if status is None or status.content_id is None:
#                return
#
#            # Detect if someone else is casting. If url of content has pcloud, we're safe
#            if status.content_id.find('pcloud') == -1:
#                self.callback_another_cast_started()
#
#    def __init__(self, update_time_secs, img_provider, chromecast):
#        self.update_time_secs, self.img_provider, self.chromecast = \
#                update_time_secs, img_provider, chromecast
#
#        self.scheduler = BackgroundScheduler()
#        self.sched_job_obj = None
#        chromecast.register_status_listener(pCloudCastSlideshow.CC_Listener(self._on_someone_else_casting))
#        self.scheduler.start()
#
#    def start(self):
#        if self.sched_job_obj is None:
#            logger.debug("Start pCloudCastSlideshow")
#            # Force a fist image update; otherwise the scheduler will only
#            # trigger the job after the first interval
#            self.show_image()
#            self.sched_job_obj = self.scheduler.add_job(func=self.show_image,
#                                   trigger="interval", seconds=self.update_time_secs)
#
#    def _on_someone_else_casting(self):
#        if self.sched_job_obj is not None:
#            logger.info("Someone started casting: stop pCloud slideshow")
#            self.stop()
#
#    def stop(self):
#        if self.sched_job_obj is not None:
#            logger.debug("Stop pCloudCastSlideshow")
#            self.sched_job_obj.remove()
#            self.sched_job_obj = None
#
#    def shutdown(self):
#        logger.debug("Shutdown pCloudCastSlideshow")
#        self.scheduler.shutdown(wait=False)
#
#
#def build_pcloud_slideshow_from_cfg(CFG, chromecast, flask_app):
#    auth = pCloudAuth(CFG['client_id'], CFG['client_secret'], CFG['auth_cache_file'])
#    img_provider = pCloudWgetImg(auth, CFG["slideshow"]["cache_file"],
#                                       CFG["slideshow"]["src_paths"],
#                                       CFG["slideshow"]["extensions_filter"])
#    slideshow = pCloudCastSlideshow(int(CFG["slideshow"]["update_image_secs"]), img_provider, chromecast)
#
#    @flask_app.route('/pcloud_slideshow/auth/step1')
#    def flask_ep_pcloud_slideshow_auth_step1():
#        return "<a href='{}'>Auth pCloud</a>".format(slideshow.img_provider.auth.get_auth_step1())
#
#    @flask_app.route('/pcloud_slideshow/auth/step2/<code>')
#    def flask_ep_pcloud_slideshow_auth_step2(code):
#        return slideshow.img_provider.auth.get_auth_step2(code)
#
#    @flask_app.route('/pcloud_slideshow/images/refresh_cache')
#    def flask_ep_pcloud_slideshow_images_refresh_cache():
#        slideshow.img_provider.refresh_cached_file_list()
#        return "OK"
#
#    @flask_app.route('/pcloud_slideshow/images/random')
#    def flask_ep_pcloud_slideshow_images_random():
#        return slideshow.img_provider.get_random_img_url()
#
#    @flask_app.route('/pcloud_slideshow/start')
#    def flask_ep_pcloud_slideshow_start():
#        slideshow.start()
#        return "OK"
#
#    @flask_app.route('/pcloud_slideshow/stop')
#    def flask_ep_pcloud_slideshow_stop():
#        slideshow.stop()
#        return "OK"
#
#    return slideshow
#
