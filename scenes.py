import json
from apscheduler.schedulers.background import BackgroundScheduler

import logging
logger = logging.getLogger('BatHome')

class SceneHandler(object):
    def __init__(self, flask_app, world):
        self._groovy_ref = None
        self.world = world
        self.scenes = [x for x in dir(self) if not x.startswith('_')]

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
        self.world.get_thing_by_name('DeskLamp').set_brightness(60, broadcast_update=False)
        self.world.get_thing_by_name('DeskLamp').set_rgb('ED7F0C', broadcast_update=False)
        self.world.get_thing_by_name('DeskLamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Floorlamp').set_brightness(100, broadcast_update=False)
        self.world.get_thing_by_name('Floorlamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Livingroom Lamp').set_brightness(100, broadcast_update=False)
        self.world.get_thing_by_name('Livingroom Lamp').broadcast_new_state(transition_time=3)

    def dinner(self):
        self.world.get_thing_by_name('Baticueva TV').stop()
        self.world.get_thing_by_name('DeskLamp').set_brightness(30, broadcast_update=False)
        self.world.get_thing_by_name('DeskLamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Floorlamp').set_brightness(100, broadcast_update=False)
        self.world.get_thing_by_name('Floorlamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Livingroom Lamp').light_off(broadcast_update=False)
        self.world.get_thing_by_name('Livingroom Lamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Kitchen Counter - Right').set_brightness(50, broadcast_update=False)
        self.world.get_thing_by_name('Kitchen Counter - Right').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Kitchen Counter - Left').set_brightness(80, broadcast_update=False)
        self.world.get_thing_by_name('Kitchen Counter - Left').broadcast_new_state(transition_time=3)

    def sleepy(self):
        self.stop_all_media_players()
        self.world.get_thing_by_name('DeskLamp').set_brightness(20, broadcast_update=False)
        self.world.get_thing_by_name('DeskLamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Floorlamp').set_brightness(20, broadcast_update=False)
        self.world.get_thing_by_name('Floorlamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Livingroom Lamp').light_off(broadcast_update=False)
        self.world.get_thing_by_name('Livingroom Lamp').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Kitchen Counter - Right').set_brightness(40, broadcast_update=False)
        self.world.get_thing_by_name('Kitchen Counter - Right').broadcast_new_state(transition_time=3)
        self.world.get_thing_by_name('Kitchen Counter - Left').light_off(broadcast_update=False)
        self.world.get_thing_by_name('Kitchen Counter - Left').broadcast_new_state(transition_time=3)

    def world_off(self):
        self.stop_all_media_players()
        for light in self.world.get_things_supporting(['light_off']):
            light.light_off(broadcast_update=False)
            light.broadcast_new_state(transition_time=5)
            logger.info("Light {} off".format(light.get_id()))

    def stop_all_media_players(self):
        for player in self.world.get_things_supporting(['stop']):
            try:
                player.stop()
                logger.info("Stopping player {}".format(player.get_id()))
            except:
                logger.info("Failed stopping player {}".format(player.get_id()))

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
            self._groovy_ref.shutdown()
            self._groovy_ref = None
        else:
            g = Groovy(self.world.get_thing_by_name('DeskLamp'))
            self._groovy_ref = BackgroundScheduler()
            self._groovy_ref.add_job(func=g.doit, trigger="interval", seconds=6)
            self._groovy_ref.start()


