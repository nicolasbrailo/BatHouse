from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing, Lamp, DimmableLamp, ColorDimmableLamp, ColorTempDimmableLamp, Button

import threading
import time

# Use the same logger as ZMF things
import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')

class MyIkeaButton2(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            self.world.get_thing_by_name('Pieza').set_brightness(30)
            return True
        if action == 'arrow_right_click':
            self.world.get_thing_by_name('Pieza').light_off()
            return True
        if action == 'brightness_down_click':
            self.world.get_thing_by_name('Lampara pasillo').set_brightness(30)
            return True
        if action == 'arrow_left_click':
            self.world.get_thing_by_name('Lampara pasillo').light_off()
            return True
        if action == 'toggle':
            self.scenes.all_lights_off()
            return True

        logger.warning("Unknown action: Ikea button - ", action)
        

class MyIkeaButton(Button):
    def __init__(self, mqtt_id, world):
        super().__init__(mqtt_id)
        self.world = world
        self.l1 = world.get_thing_by_name('Livingroom Table Lamp')
        self.l2 = world.get_thing_by_name('Livingroom Couch Lamp')

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            self.l1.set_brightness(100)
            self.l2.set_brightness(100)
            return True
        if action == 'arrow_right_click':
            self.l1.set_brightness(75)
            self.l2.set_brightness(75)
            return True
        if action == 'brightness_down_click':
            self.l1.set_brightness(50)
            self.l2.set_brightness(50)
            return True
        if action == 'arrow_left_click':
            self.l1.set_brightness(25)
            self.l2.set_brightness(25)
            return True
        if action == 'toggle':
            if self.l1.is_on or self.l2.is_on:
                self.l1.light_off()
                self.l2.light_off()
            else:
                self.l2.set_brightness(20)
            return True

        logger.warning("Unknown action: Ikea button - ", action)
        

class HoldActionHelper(object):
    def __init__(self):
        self.cb = None
        self.sleep_secs = None
        self.should_run = False
        self.thread = None

    def start(self, sleep_secs, cb):
        if self.thread is not None:
            # We may receive duplicated message to start up. Ignore!
            return True

        self.cb = cb
        self.sleep_secs = sleep_secs

        def sleepy_loop():
            while self.should_run:
                cb()
                time.sleep(sleep_secs)

        self.thread = threading.Thread(target=sleepy_loop)
        self.should_run = True
        self.thread.start()

    def stop(self):
        if self.thread is not None:
            self.should_run = False
            self.thread.join()
            self.thread = None


class MediaActionHelper(object):
    def __init__(self, world):
        self.world = world

    def all_vol_up(self):
        for player in self.world.get_things_supporting(['volume_up']):
            player.volume_up()

    def all_vol_down(self):
        for player in self.world.get_things_supporting(['volume_down']):
            player.volume_down()

    def all_stop(self):
        for player in self.world.get_things_supporting(['stop']):
            player.stop()


class HueButton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes
        self.media_actions = MediaActionHelper(world)
        self.hold_action = HoldActionHelper()

    def handle_action(self, action, msg):
        if action == 'up-hold':
            self.hold_action.start(0.15, self.media_actions.all_vol_up)
            return True
        if action == 'up-hold-release':
            self.hold_action.stop()
            return True
        if action == 'up-press':
            self.media_actions.all_vol_up()
            return True

        if action == 'down-hold':
            self.hold_action.start(0.15, self.media_actions.all_vol_down)
            return True
        if action == 'down-hold-release':
            self.hold_action.stop()
            return True
        if action == 'down-press':
            self.media_actions.all_vol_down()
            return True

        if action == 'off-hold':
            self.scenes.all_lights_off()
            return True

        if action == 'off-press':
            self.media_actions.all_stop()
            self.scenes.all_lights_off()
            return True

        if action == 'on-press':
            self.world.get_thing_by_name('Livingroom Table Lamp').set_brightness(50)
            self.world.get_thing_by_name('Livingroom Couch Lamp').set_brightness(90)
            self.world.get_thing_by_name('Cuarto Olivia').set_brightness(60)
            self.world.get_thing_by_name('Lampara pasillo').set_brightness(75)
            return True


        logger.warning("No handler for action {} message {}".format(action, msg))
        return False


class RoundIkeaButton(Button):
    def __init__(self, mqtt_id, world):
        super().__init__(mqtt_id)
        self.world = world

    def handle_action(self, action, msg):
        if action in ['rotate_left', 'rotate_right']:
            vol_pct = 100 * int(msg['brightness']) / 255
            for player in self.world.get_things_supporting(['volume_down']):
                logger.debug("Set player {} to {}% vol".format(player.get_id(), vol_pct))
                player.set_volume_pct(vol_pct)
            return True
        logger.warning("No handler for action {} message {}".format(action, msg))
        return False


def register_all_things(world, scenes):
    world.register_thing(DimmableLamp('Livingroom Table Lamp', world.mqtt))
    world.register_thing(ColorDimmableLamp('Livingroom Couch Lamp', world.mqtt))
    world.register_thing(ColorDimmableLamp('Pasillo', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('Cuarto Olivia', world.mqtt))
    world.register_thing(DimmableLamp('Pieza', world.mqtt))
    #world.register_thing(DimmableLamp('Dead lamp', world.mqtt))

    world.register_thing(MyIkeaButton('IkeaButton', world))
    world.register_thing(MyIkeaButton2('Otro IkeaButton', world, scenes))
    world.register_thing(HueButton(   'HueButton', world, scenes))
    world.register_thing(RoundIkeaButton('RoundIkeaButton', world))

