from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Button
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import ColorDimmableLamp
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import ColorTempDimmableLamp
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import DimmableLamp
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Lamp
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import MotionActivatedNightLight
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import MultiThing
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing

from zigbee2mqtt2flask.zigbee2mqtt2flask.geo_helper import light_outside
from zigbee2mqtt2flask.zigbee2mqtt2flask.geo_helper import late_night

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

import datetime
import threading
import time

# Use the same logger as ZMF things
import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')


MY_LAT=51.5464371
MY_LON=0.111148
LATE_NIGHT_START_HOUR=22

def is_it_light_outside():
    return light_outside(MY_LAT, MY_LON)

def is_it_late_night():
    return late_night(MY_LAT, MY_LON, LATE_NIGHT_START_HOUR)

class KitchenBoton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            if self.world.get_thing_by_name('Spotify').json_status()['active_device'] != 'Portalcito':
                self.world.get_thing_by_name('Spotify').play_in_device('Portalcito')
                logger.info("Transfer Spotify to Portalcito")
            else:
                self.world.get_thing_by_name('Spotify').playpause()
            return True
        if action == 'brightness_down_click':
            if self.world.get_thing_by_name('KitchenSpot1').is_on:
                self.world.get_thing_by_name('KitchenSpot1').light_off()
            else:
                self.world.get_thing_by_name('KitchenSpot1').set_brightness(100)
            return True
            return True
        if action == 'arrow_right_click':
            if self.world.get_thing_by_name('Spotify').json_status()['active_device'] == 'Portalcito':
                self.world.get_thing_by_name('Spotify').play_next_in_queue()
            return True
        if action == 'arrow_left_click':
            if self.world.get_thing_by_name('Spotify').json_status()['active_device'] == 'Portalcito':
                self.world.get_thing_by_name('Spotify').play_prev_in_queue()
            return True
        if action == 'toggle':
            if self.world.get_thing_by_name('KitchenStandLamp').is_on:
                self.world.get_thing_by_name('KitchenStandLamp').light_off()
            else:
                self.world.get_thing_by_name('KitchenStandLamp').set_brightness(100)
            return True

        logger.warning("Unknown action: Ikea button - " + str(action))

class BatipiezaBoton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'release':
            return True
        if action == 'on':
            return True
        if action == 'press':
            if self.world.get_thing_by_name('Belador').is_on or \
                    self.world.get_thing_by_name('Snoopy').is_on or \
                    self.world.get_thing_by_name('BaticomedorFloorlampL').is_on:
                time.sleep(2)
                self.scenes.all_lights_off(all_except=['OlmaLamp'])
            else:
                self.world.get_thing_by_name('Belador').set_brightness(10)
            return True
        return False

class BotonComedorHue(Button):
    def __init__(self, mqtt_id, world):
        super().__init__(mqtt_id)
        self.world = world

    def handle_action(self, action, msg):
        if action == 'on_press':
            if self.world.get_thing_by_name('Snoopy').is_on:
                self.world.get_thing_by_name('Comedor').light_off()
                self.world.get_thing_by_name('Snoopy').light_off()
            else:
                self.world.get_thing_by_name('Comedor').set_brightness(100)
                self.world.get_thing_by_name('Snoopy').set_brightness(50)
            return True
        if action == 'on_hold':
                self.world.get_thing_by_name('Comedor').set_brightness(100)
                self.world.get_thing_by_name('Snoopy').set_brightness(100)
        if action == 'off_press':
            if self.world.get_thing_by_name('CocinaCountertop').is_on or self.world.get_thing_by_name('LandingPB').is_on:
                # Ignore: it's confusing to toggle state because it can't be seen
                pass
            else:
                self.world.get_thing_by_name('CocinaCountertop').set_brightness(100)
                self.world.get_thing_by_name('LandingPB').set_brightness(50)
            return True
        if action == 'up_press':
            return True
        if action == 'down_press':
            return True
        if action == 'on_hold_release':
            return True
        if action == 'off_hold':
            return True
        if action == 'off_hold_release':
            return True
        if action == 'up_hold':
            return True
        if action == 'up_hold_release':
            return True
        if action == 'down_hold':
            return True
        if action == 'down_hold_release':
            return True
        return False

class NicofficeBoton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'brightness_up_click':
            self.world.get_thing_by_name('Spotify').volume_up()
            return True
        if action == 'brightness_down_click':
            self.world.get_thing_by_name('Spotify').volume_down()
            return True
        if action == 'toggle':
            self.world.get_thing_by_name('Spotify').playpause()
            return True
        if action == 'toggle_hold':
            sp = self.world.get_thing_by_name('Spotify')
            sp_st = sp.json_status()
            dev_active = sp_st['active_device']
            known_devs = sp_st['available_devices']
            devs_to_skip = ['Baticomedor TV'] # Hardcoded list of devices to never use for Spotify
            available_devs = [x for x in known_devs if x != dev_active and x not in devs_to_skip]

            logger.info("Spotify active device is " + str(dev_active))
            for dev in known_devs:
                can_play =  ' (can transfer playback)' if dev in available_devs else " (can't transfer playback)"
                logger.info("\tKnown devices: " + str(dev) + can_play)

            if len(available_devs) > 0:
                logger.info("Transferring Spotify playback to " + str(available_devs[0]))
                sp.play_in_device(available_devs[0])

            return True
        if action == 'arrow_right_click':
            self.world.get_thing_by_name('Spotify').play_next_in_queue()
            return True
        if action == 'arrow_left_click':
            self.world.get_thing_by_name('Spotify').play_prev_in_queue()
            return True

        logger.warning("Unknown action: Ikea button - " + str(action))


class Cronenberg(Thing):
    def __init__(self, world):
        super().__init__('Cronenberg')
        self.managing_emlivia_night_light = False
        self.world = world
        self._cron = BackgroundScheduler()
        self._cron_jon = self._cron.add_job(func=self._tick, trigger=IntervalTrigger(minutes=15))
        self._cron.start()

    def json_status(self):
        return {}

    def _tick(self):
        light = self.world.get_thing_by_name('OlmaVelador')

        local_hour = datetime.datetime.now().hour # no tz, just local hour
        emlivia_night = local_hour >= 21 or local_hour < 8

        logger.info("Cronenberg tick at {} hrs. Nighttime? {} Day out? {} Managing light? {}".format(local_hour, emlivia_night, is_it_light_outside(), self.managing_emlivia_night_light))

        if not is_it_light_outside() and emlivia_night and not self.managing_emlivia_night_light:
            logger.info("Emlivia night light ON")
            light.set_brightness(10)
            self.managing_emlivia_night_light = True

        elif self.managing_emlivia_night_light and is_it_light_outside():
            logger.info("Emlivia night light OFF")
            self.managing_emlivia_night_light = False
            light.light_off()

def register_all_things(world, scenes):
    world.register_thing(Cronenberg(world))

    world.register_thing(DimmableLamp('CocinaCountertop', world.mqtt))

    world.register_thing(DimmableLamp('LandingPB', world.mqtt))
    world.register_thing(DimmableLamp('EscaleraPB', world.mqtt))
    world.register_thing(DimmableLamp('EscaleraP1', world.mqtt))
    world.register_thing(MotionActivatedNightLight(MY_LAT, MY_LON, LATE_NIGHT_START_HOUR, world,
                                     ['EscaleraPBSensor1', 'EscaleraPBSensor2'],
                                      world.get_thing_by_name('EscaleraPB')))

    world.register_thing(ColorDimmableLamp('Belador', world.mqtt))
    world.register_thing(DimmableLamp('NicoVelador', world.mqtt))
    world.register_thing(BatipiezaBoton('BeladorBoton', world, scenes))

    world.register_thing(DimmableLamp('Oficina', world.mqtt))

    # 'Comedor' is a multithing, and member variables don't seem to work with multithing (they are funcs instead)
    # Only functions can be called on multithings
    world.register_thing(MultiThing('Comedor', ColorDimmableLamp, ['ComedorL', 'ComedorR'], world.mqtt))
    world.register_thing(DimmableLamp('Snoopy', world.mqtt))
    world.register_thing(BotonComedorHue('BotonComedor', world))

    world.register_thing(ColorDimmableLamp('OlmaVelador', world.mqtt))

    #world.register_thing(BaticomedorBoton('BaticomedorBoton', world, scenes))
    #world.register_thing(ColorTempDimmableLamp('NicofficeSpotLamp', world.mqtt))
    #world.register_thing(NicofficeBoton('NicofficeBoton', world, scenes))
    #world.register_thing(KitchenBoton('KitchenBoton', world, scenes))

