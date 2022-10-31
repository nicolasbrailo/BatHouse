import os
import json
from apscheduler.schedulers.background import BackgroundScheduler

import logging
logger = logging.getLogger('BatHome')

def shutdown_baticueva_tv():
    cmd = "/home/pi/kryten/shutdown_baticueva_tv.sh"
    logger.info("Trying to shutdown Baticueva TV using Google assistant. Hopefully command log follows.")
    logger.info("Run " + cmd)
    os.system(cmd)
    logger.info("Finish trying to shutdown Baticueva TV using Google assistant.")


class SceneHandler(object):
    def __init__(self, flask_app, world):
        self.scenes = [x for x in dir(self) if not x.startswith('_')]
        self._groovy_ref = None
        self.fake_players = []
        self.world = world

        @flask_app.route('/scenes/list')
        def flask_endpoint_get_scenes():
            return json.dumps(self.scenes)

        @flask_app.route('/scene_set/<name>')
        def flask_endpoint_set_scene(name):
            logger.info("User requested scene {}".format(name))
            m = getattr(self, name, None)
            if m is None:
                return "No scene {}".format(action, thing_name), 405

            m()
            return "OK"

    def living_room_evening(self):
        self.world.get_thing_by_name('BaticomedorLamp').set_brightness(100, broadcast_update=False)
        self.world.get_thing_by_name('BaticomedorLamp').set_rgb('FD6F0C', broadcast_update=False)
        self.world.get_thing_by_name('BaticomedorLamp').broadcast_new_state(transition_time=3)
        #self.world.get_thing_by_name('EntrepisoLamp').set_brightness(50, broadcast_update=False)
        #self.world.get_thing_by_name('EntrepisoLamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('BatBedsideLamp').set_brightness(30)

    def sleepy(self):
        self.world.get_thing_by_name('BaticomedorLamp').set_brightness(10, broadcast_update=False)
        self.world.get_thing_by_name('BaticomedorLamp').set_rgb('ED7F0C', broadcast_update=False)
        self.world.get_thing_by_name('BaticomedorLamp').broadcast_new_state(transition_time=3)
        #self.world.get_thing_by_name('EntrepisoLamp').set_brightness(10, broadcast_update=False)
        #self.world.get_thing_by_name('EntrepisoLamp').broadcast_new_state(transition_time=3)

    def world_off(self):
        self.stop_all_media_players()
        self.all_lights_off()

    def all_lights_off(self, all_except=[]):
        for light in self.world.get_things_supporting(['light_off']):
            if light.get_id() not in all_except:
                light.light_off(broadcast_update=True)
                logger.info("Light {} off".format(light.get_id()))

    def stop_all_media_players(self):
        for player in self.fake_players:
            player.stop()

        for player in self.world.get_things_supporting(['stop']):
            try:
                player.stop()
                logger.info("Stopping player {}".format(player.get_id()))
            except:
                logger.info("Failed stopping player {}".format(player.get_id()))

        # Try to turn TV off
        shutdown_baticueva_tv()

    def groovy(self):
        class Groovy(object):
            def __init__(self, lamp):
                self.direction = None
                self.lamp = lamp

            def doit(self):
                if self.direction == 'up':
                    col = '0000FF'
                    self.direction = 'down'
                else:
                    col = 'FF0000'
                    self.direction = 'up'

                self.lamp.set_rgb(col, broadcast_update=False)
                self.lamp.broadcast_new_state(transition_time=5)

        if self._groovy_ref is not None:
            self._groovy_job.remove()
            self._groovy_ref.shutdown(wait=False)
            self._groovy_job = None
            self._groovy_ref = None
        else:
            l = self.world.get_thing_by_name('BaticomedorLamp')
            l.set_brightness(100, broadcast_update=False)
            g = Groovy(l)
            self._groovy_ref = BackgroundScheduler()
            self._groovy_job = self._groovy_ref.add_job(func=g.doit, trigger="interval", seconds=6)
            self._groovy_ref.start()


