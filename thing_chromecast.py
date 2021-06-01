from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing

# https://github.com/balloob/pychromecast
import pychromecast
from pychromecast.controllers.youtube import YouTubeController
from apscheduler.schedulers.background import BackgroundScheduler

import json
import time

# Use the same logger as ZMF things
import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')


class ThingChromecast(Thing):
    @staticmethod
    def set_flask_bindings(flask_app, world):
        @flask_app.route('/world/scan_chromecasts')
        def flask_ep_chromecast_scan_network():
            return ThingChromecast.scan_chromecasts_and_register(world)

    @staticmethod
    def scan_chromecasts_and_register(world):
        scan_result = {}
        for cc in ThingChromecast.scan_network():
            try:
                world.register_thing(cc)
                scan_result[cc.get_id()] = 'Found new device'
            except KeyError:
                scan_result[cc.get_id()] = 'Already registered'
        return json.dumps(scan_result)


    @staticmethod
    def scan_network():
        """ Get all Chromecasts in the network """
        logger.info("Will scan 10 seconds for Chromecasts...")
        devs, bro = pychromecast.discovery.discover_chromecasts(timeout=10)
        pychromecast.discovery.stop_discovery(bro)
        logger.info(f"Found {len(devs)} Chromecasts")
        ccs, bro = pychromecast.get_listed_chromecasts(friendly_names=[d.friendly_name for d in devs])
        return [ThingChromecast(cc) for cc in ccs]

    @staticmethod
    def mk_from_ip(ip):
        try:
            return ThingChromecast(pychromecast.Chromecast(ip))
        except pychromecast.error.ChromecastConnectionError:
            return ThingChromecast(None, ip)

    def __init__(self, cc_object, ip=None):
        self._reconnect_job = None
        self._scheduler = None
        self.cc = cc_object

        # If cc_object is none but ip is known, this may be an offline CC
        if self.cc is None:
            super().__init__(f"Offline_Chromecast_{ip}")
            self._delay_try_reconnect(ip)
            self.reconnect_attempts = 0
        else:
            super().__init__(self.cc.device.friendly_name)
            self.cc.wait()

        logger.info("Found Chromecast {}".format(self.get_id()))

    def _delay_try_reconnect(self, ip=None):
        if self._reconnect_job is not None:
            logger.debug(f"Ignoring reconnection request for Chromecast {ip} - there is an ongoing reconnect attempt")
            return

        if self._scheduler is None:
            self._scheduler = BackgroundScheduler()
            self._scheduler.start()
            self._reconnect_timeout_secs = 15

        if ip is not None:
            self._reconnect_ip = ip

        self.reconnect_attempts = 0
        self._reconnect_job = self._scheduler.add_job(func=self._try_reconnect,
                               trigger="interval", seconds=self._reconnect_timeout_secs)

    def _try_reconnect(self):
        try:
            self.reconnect_attempts += 1
            logger.info(f"Trying to connect to Chromecast at {self._reconnect_ip}, attempt {self.reconnect_attempts}")
            new_cc_obj = pychromecast.Chromecast(self._reconnect_ip)

            # No exception? Success, CC is online!
            self._reconnect_job.remove()
            self._scheduler.shutdown(wait=False)
            self._reconnect_job = None
            self._scheduler = None

            self.cc = new_cc_obj
            # TODO: What will break if an object changes its own name!?
            # TODO: world.register_thing(self) ??
            self.thing_id = self.cc.device.friendly_name
            logger.info(f"Chromecast at {self._reconnect_ip} back online, now known as {self.thing_id}")
        except pychromecast.error.ChromecastConnectionError:
            logger.info(f"Chromecast at {self.get_id()} is still offline")

    def _catch_cc_disconnect(base_func):
        def wrap(self, *a, **kw):
            try:
                return base_func(self, *a, **kw)
            except pychromecast.error.NotConnected:
                # TODO: Try to recon offline cc, how?
                self.offline_cc = self.cc
                self.cc = None
                return
        return wrap

    @_catch_cc_disconnect
    def playpause(self):
        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return

        if self.cc.media_controller.is_paused:
            self.cc.media_controller.play()
        elif self.cc.media_controller.is_playing:
            self.cc.media_controller.pause()
        else:
            logger.error("Error: CC {} is not playing nor paused. Status: {}".format(
                        self.get_id(), self.cc.media_controller.status.player_state))

    @_catch_cc_disconnect
    def stop(self):
        # A bit more agressive than stop, but stop on its own seems useless:
        # cc will report its state as media still loaded but idle. Easier to kill
        self.cc.quit_app()

    @_catch_cc_disconnect
    def play_next_in_queue(self):
        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return

        self.cc.media_controller.skip()

    @_catch_cc_disconnect
    def play_prev_in_queue(self):
        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return

        self.cc.media_controller.rewind()

    @_catch_cc_disconnect
    def toggle_mute(self):
        self.cc.set_volume_muted(not self.cc.status.volume_muted)

    @_catch_cc_disconnect
    def volume_up(self):
        self.cc.volume_up()

    @_catch_cc_disconnect
    def volume_down(self):
        self.cc.volume_down()

    @_catch_cc_disconnect
    def set_volume_pct(self, vol):
        self.cc.set_volume(int(vol) / 100)

    @_catch_cc_disconnect
    def set_playtime(self, t):
        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return

        pause_after_seek = self.cc.media_controller.is_paused
        self.cc.media_controller.seek(t)
        if pause_after_seek:
            self.cc.media_controller.pause()

    @_catch_cc_disconnect
    def youtube(self, video_id):
        yt = YouTubeController()
        self.cc.register_handler(yt)
        yt.play_video(video_id)

    @_catch_cc_disconnect
    def show_image(self, url):
        self.cc.play_media(url=url, content_type='image/jpeg')

    @_catch_cc_disconnect
    def play_local(self):
        # Deploy file to local and send to chromecast
        # https://stackoverflow.com/questions/43580/how-to-find-the-mime-type-of-a-file-in-python
        # Get mime type: file --mime-type -b
        self.cc.play_media(url='http://192.168.1.50/webapp/bartolito.mkv', content_type='video/x-matroska')

    @_catch_cc_disconnect
    def register_status_listener(self, listener):
        self.cc.media_controller.register_status_listener(listener)

    def supported_actions(self):
        return ['playpause', 'stop', 'play_next_in_queue', 'play_prev_in_queue',
                'toggle_mute', 'volume_up', 'volume_down', 'set_volume_pct',
                'set_playtime', 'youtube', 'show_image', 'show_media']

    def json_status(self):
        if self.cc is None:
            self._delay_try_reconnect()
            return {
                    'name': self.get_id(),
                    'offline': True,
                    'player_state': 'Offline',
                    'media': None,
                }

        if self.cc.status is None:
            logger.warning("CC {} was disconected? Trying to reconnect.".format(self.get_id()))
            self.cc.wait()
            self.cc_offline = False

        status = {
                'name': self.get_id(),
                'offline': False,
                'uri': self.cc.uri,
                'app': self.cc.status.display_name,
                'volume_pct': int(100 * self.cc.status.volume_level),
                'volume_muted': self.cc.status.volume_muted,
                'player_state': 'Idle',
                'media': None,
            }

        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return status

        status['player_state'] = self.cc.media_controller.status.player_state
        status['media'] = {
                    'icon': None,
                    'title': self.cc.media_controller.status.title,
                    'duration': self.cc.media_controller.status.duration,
                    'current_time': self.cc.media_controller.status.current_time,
                }

        icons = [img.url for img in self.cc.media_controller.status.images if img is not None]
        try:
            status['media']['icon'] = icons[0]
        except:
            pass

        return status


