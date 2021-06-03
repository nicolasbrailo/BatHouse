import time

import logging
logger = logging.getLogger('BatHome')

from apscheduler.schedulers.background import BackgroundScheduler

class ChromecastSlideshow():
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

    def __init__(self, world, cc_name, img_uri_provider):
        self.world = world
        self.cc_name = cc_name
        self.cc = None
        self.img_uri_provider = img_uri_provider

        self.bg_job = None
        self.update_time_secs = 60
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def _try_connect(base_func):
        def wrap(self, *a, **kw):
            if self.cc is None:
                self.cc = self.world.get_thing_by_name(self.cc_name)

            if self.cc is None:
                logger.warning("Ignoring {str(self.base_func} for {self.cc_name}: not connected")
                return None
            else:
                self.cc.register_status_listener(ChromecastSlideshow.CC_Listener(self._on_someone_else_casting))
                return base_func(self, *a, **kw)

        return wrap

    def _on_someone_else_casting(self):
        if self.bg_job is not None:
            logger.info("Someone started casting: stopping slideshow")
            self.stop_slideshow()

    @_try_connect
    def show_image(self):
        url = self.img_uri_provider.get_random_img_url() + "?nocache=" + str(time.time())
        logger.debug("Asking {} to show image {}".format(self.cc_name, url))
        self.cc.show_image(url)
        return url

    @_try_connect
    def start(self):
        if self.bg_job is not None:
            logger.info("Start slideshow requested, but a slideshow is already in progress")
        else:
            logger.debug("Starting slideshow")
            # Force a first image update; otherwise the scheduler will only
            # trigger the job after the first interval
            self.show_image()
            self.bg_job = self.scheduler.add_job(func=self.show_image,
                                   trigger="interval", seconds=self.update_time_secs)

    def stop(self):
        if self.bg_job is not None:
            logger.debug("Stopping slideshow")
            self.bg_job.remove()
            self.bg_job = None

    def shutdown(self):
        logger.debug("Shutdown slideshow")
        self.scheduler.shutdown(wait=False)


def build_slideshow_and_register_to_flask(flask, flask_api_url_prefix, img_uri_provider, world, cc_name):
    cs = ChromecastSlideshow(world, cc_name, img_uri_provider)

    @flask.route(flask_api_url_prefix)
    @flask.route(flask_api_url_prefix + '/show_image')
    def idx():
        url = cs.show_image()
        return "Showing " + url

    @flask.route(flask_api_url_prefix + '/start')
    def start_new_ss():
        cs.start()
        return "Starting slideshow on " + cc_name

    @flask.route(flask_api_url_prefix + '/stop')
    def stop_ss():
        cs.stop()
        return "Stop slideshow on " + cc_name

