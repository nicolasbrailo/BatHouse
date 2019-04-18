from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Button

import threading
import time

class MyIkeaButton(Button):
    def __init__(self, mqtt_id, pretty_name, world):
        super().__init__(mqtt_id, pretty_name)
        self.world = world
        self.l1 = world.get_thing_by_name('Kitchen Counter - Left')
        self.l2 = world.get_thing_by_name('Kitchen Counter - Right')

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

        print("Unknown action: Ikea button - ", action)
        

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
    def __init__(self, mqtt_id, pretty_name, world, scenes):
        super().__init__(mqtt_id, pretty_name)
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

        if action == 'off-press':
            self.media_actions.all_stop()
            return True

        if action == 'on-press':
            self.world.get_thing_by_name('Spotify').playpause()
            return True

        print("No handler for action {} message {}".format(action, msg))
        return False
    
