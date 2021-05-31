from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing, Lamp, DimmableLamp, ColorDimmableLamp, ColorTempDimmableLamp, Button

import threading
import time

# Use the same logger as ZMF things
import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')

class IkeaButton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            return True
        if action == 'arrow_right_click':
            return True
        if action == 'brightness_down_click':
            return True
        if action == 'arrow_left_click':
            return True
        if action == 'toggle':
            if self.world.get_thing_by_name('BaticomedorLamp').is_on or \
                    self.world.get_thing_by_name('EmliviaRoomLamp').is_on or \
                    self.world.get_thing_by_name('BatBedsideLamp').is_on or \
                    self.world.get_thing_by_name('EntrepisoLamp').is_on:
                time.sleep(3)
                self.scenes.all_lights_off()
            else:
                self.world.get_thing_by_name('BaticomedorLamp').set_brightness(10)
                self.world.get_thing_by_name('EntrepisoLamp').set_brightness(10)
            return True

        logger.warning("Unknown action: Ikea button - ", action)


class IkeaButton2(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            return True
        if action == 'arrow_right_click':
            return True
        if action == 'brightness_down_click':
            return True
        if action == 'arrow_left_click':
            return True
        if action == 'toggle':
            return True

        logger.warning("Unknown action: Ikea button - ", action)

def register_all_things(world, scenes):
    world.register_thing(ColorDimmableLamp('BaticomedorLamp', world.mqtt))
    world.register_thing(ColorDimmableLamp('EmliviaRoomLamp', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('EntrepisoLamp', world.mqtt))
    world.register_thing(DimmableLamp('BatiofficeDeskLamp', world.mqtt))
    world.register_thing(DimmableLamp('BatBedsideLamp', world.mqtt))
    world.register_thing(IkeaButton('BotonIkeaBelen', world, scenes))
    world.register_thing(IkeaButton2('BotonIkeaComedor', world, scenes))

