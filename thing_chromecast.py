from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing

# https://github.com/balloob/pychromecast
import pychromecast
from pychromecast.controllers.youtube import YouTubeController

import json

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
        logger.info("Scanning for ChromeCasts")
        return [ThingChromecast(cc) for cc in pychromecast.get_chromecasts()]

    @staticmethod
    def mk_from_ip(ip):
        return ThingChromecast(pychromecast.Chromecast(ip))

    def __init__(self, cc_object):
        self.cc = cc_object
        thing_id = self.cc.device.friendly_name
        super().__init__(thing_id)

        cc_object.start()
        logger.info("Found Chromecast {}".format(thing_id))

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

    def stop(self):
        # A bit more agressive than stop, but stop on its own seems useless:
        # cc will report its state as media still loaded but idle. Easier to kill
        self.cc.quit_app()

    def play_next_in_queue(self):
        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return

        self.cc.media_controller.skip()

    def play_prev_in_queue(self):
        try:
            self.cc.media_controller.update_status()
        except pychromecast.error.UnsupportedNamespace:
            # No media running
            return

        self.cc.media_controller.rewind()

    def toggle_mute(self):
        self.cc.set_volume_muted(not self.cc.status.volume_muted)

    def volume_up(self):
        self.cc.volume_up()

    def volume_down(self):
        self.cc.volume_down()

    def set_volume_pct(self, vol):
        self.cc.set_volume(int(vol) / 100)

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


    def youtube(self, video_id):
        yt = YouTubeController()
        self.cc.register_handler(yt)
        yt.play_video(video_id)

    def show_image(self, url):
        self.cc.play_media(url=url, content_type='image/jpeg')

    def play_local(self):
        # Deploy file to local and send to chromecast
        # https://stackoverflow.com/questions/43580/how-to-find-the-mime-type-of-a-file-in-python
        # Get mime type: file --mime-type -b
        self.cc.play_media(url='http://192.168.2.100:1234/webapp/bartolito.mkv', content_type='video/x-matroska')

    def register_status_listener(self, listener):
        self.cc.media_controller.register_status_listener(listener)

    def supported_actions(self):
        return ['playpause', 'stop', 'play_next_in_queue', 'play_prev_in_queue',
                'toggle_mute', 'volume_up', 'volume_down', 'set_volume_pct',
                'set_playtime', 'youtube', 'show_image', 'show_media']

    def json_status(self):
        if self.cc.status is None:
            logger.warning("CC {} was disconected? Trying to reconnect.".format(self.get_id()))
            self.cc.start()

        status = {
                'name': self.get_id(),
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


