from zigbee2mqtt2flask.zigbee2mqtt2flask.things import *
from zigbee2mqtt2flask.zigbee2mqtt2flask.geo_helper import *

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


class BeladorBoton(Button):
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
            if any_light_on(self.world, ['Belador', 'Snoopy', 'NicoVelador', 'Comedor']):
                time.sleep(2)
                self.scenes.all_lights_off(all_except=['OlmaVelador'])
            else:
                self.world.get_thing_by_name('Belador').set_brightness(10)
        return True


class BatipiezaBoton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'on':
            light_group_toggle(self.world, [
                    ('Belador', 30),
                    ('NicoVelador', 25),
                ]);
        if action == 'off':
            self.world.get_thing_by_name('EscaleraP1').light_toggle(brightness=25)
        return True


class BotonComedorHue(Button):
    def __init__(self, mqtt_id, world):
        super().__init__(mqtt_id)
        self.world = world

    def handle_action(self, action, msg):
        if action == 'on_press':
            light_group_toggle(self.world, [
                    ('Snoopy', 50),
                    ('Comedor', 60),
                ]);
            return True
        if action == 'on_hold':
            light_group_toggle(self.world, [
                    ('Snoopy', 100),
                    ('Comedor', 100),
                ]);
            return True
        if action == 'off_press':
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


class BotonCocina(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'on':
            self.world.get_thing_by_name('CocinaCeiling').light_toggle(brightness=100)
        if action == 'off':
            light_group_toggle(self.world, [
                    ('CocinaCountertop', 100),
                    ('LandingPB', 30),
                ]);
        return True

class LeavingRoutine:
    def __init__(self, world, scenes):
        self.world = world
        self.scenes = scenes
        self._scheduler = None
        self.timeout_secs = 60 * 4
        self.managed_things = [('ComedorII', 100), ('LandingPB', 100), ('EscaleraPB', 50)]

    def trigger_leaving_routine(self):
        logger.warning("Leaving home scene on")
        if self._scheduler is not None:
            self._bg.remove()

        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        self._bg = self._scheduler.add_job(func=self._timeout,
                               trigger="interval", seconds=self.timeout_secs)

        for t,pct in self.managed_things:
            self.world.get_thing_by_name(t).set_brightness(pct)

    def _timeout(self):
        logger.info("Leaving timeout: shutdown all managed lights")
        for t,_pct in self.managed_things:
            self.world.get_thing_by_name(t).light_off()
        self._bg.remove()
        self._scheduler = None

class BotonEntrada(Button):
    def __init__(self, mqtt_id, world, scenes, leaving_routine):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes
        self.leaving_routine = leaving_routine

    def handle_action(self, action, msg):
        if action == 'toggle':
            self.leaving_routine.trigger_leaving_routine()
            return True
        if action == 'brightness_up_click':
            self.world.get_thing_by_name('Comedor').set_brightness(50)
            self.world.get_thing_by_name('Snoopy').set_brightness(30)
            return True
        if action == 'brightness_down_click':
            self.scenes.all_lights_off(all_except=['ComedorII', 'LandingPB'])
            try:
                self.world.get_thing_by_name('Spotify').stop()
            except:
                logger.warning("Spotify not enabled, can't stop it")
            try:
                self.world.get_thing_by_name('Sonos').stop()
            except:
                logger.warning("Sonos not enabled, can't stop it")
            return True
        if action == 'toggle_hold':
            self.scenes.world_off()
            return True
        if action == 'arrow_right_click':
            return True
        if action == 'arrow_left_click':
            return True
        logger.warning("Unknown action: Ikea RC button - " + str(action))
        return True


#class NicofficeBoton(Button):
#    def __init__(self, mqtt_id, world, scenes):
#        super().__init__(mqtt_id)
#        self.world = world
#        self.scenes = scenes
#
#    def handle_action(self, action, msg):
#        if action == 'brightness_up_click':
#            self.world.get_thing_by_name('Spotify').volume_up()
#            return True
#        if action == 'brightness_down_click':
#            self.world.get_thing_by_name('Spotify').volume_down()
#            return True
#        if action == 'toggle':
#            self.world.get_thing_by_name('Spotify').playpause()
#            return True
#        if action == 'toggle_hold':
#            sp = self.world.get_thing_by_name('Spotify')
#            sp_st = sp.json_status()
#            dev_active = sp_st['active_device']
#            known_devs = sp_st['available_devices']
#            devs_to_skip = ['Baticomedor TV'] # Hardcoded list of devices to never use for Spotify
#            available_devs = [x for x in known_devs if x != dev_active and x not in devs_to_skip]
#
#            logger.info("Spotify active device is " + str(dev_active))
#            for dev in known_devs:
#                can_play =  ' (can transfer playback)' if dev in available_devs else " (can't transfer playback)"
#                logger.info("\tKnown devices: " + str(dev) + can_play)
#
#            if len(available_devs) > 0:
#                logger.info("Transferring Spotify playback to " + str(available_devs[0]))
#                sp.play_in_device(available_devs[0])
#
#            return True
#        if action == 'arrow_right_click':
#            self.world.get_thing_by_name('Spotify').play_next_in_queue()
#            return True
#        if action == 'arrow_left_click':
#            self.world.get_thing_by_name('Spotify').play_prev_in_queue()
#            return True
#
#        logger.warning("Unknown action: Ikea button - " + str(action))


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


class SensorPuertaEntrada(DoorOpenSensor):
    def __init__(self, mqtt_id, leaving_routine):
        self.door_open_timeout_secs = 60
        super().__init__(mqtt_id, self.door_open_timeout_secs)
        self.leaving_routine = leaving_routine

    def door_closed(self):
        logger.info("Puerta cerrada: " + str(self.json_status()))

    def door_opened(self):
        logger.info("Puerta abierta: " + str(self.json_status()))
        if not is_it_light_outside():
            logger.info("No light outside, trigger leaving routine")
            self.leaving_routine.trigger_leaving_routine()

    def door_open_timeout(self):
        logger.info("Door open after timeout expired...")
        #TODO Flash all lights


def register_all_things(world, scenes):
    #world.register_thing(Cronenberg(world))
    leaving_routine = LeavingRoutine(world, scenes)

    world.register_thing(BotonCocina('BotonCocina', world, scenes))
    world.register_thing(MultiThing('CocinaCountertop', DimmableLamp,
                                   ['CocinaCountertop1', 'CocinaCountertop2'], world.mqtt))
    world.register_thing(DimmableLamp('CocinaCeiling', world.mqtt))

    world.register_thing(BotonEntrada('BotonEntrada', world, scenes, leaving_routine))
    world.register_thing(DimmableLamp('ComedorII', world.mqtt))
    world.register_thing(SensorPuertaEntrada('SensorPuertaEntrada', leaving_routine))

    world.register_thing(DimmableLamp('LandingPB', world.mqtt))
    world.register_thing(DimmableLamp('EscaleraPB', world.mqtt))
    world.register_thing(DimmableLamp('EscaleraP1', world.mqtt))
    world.register_thing(MotionActivatedNightLight(MY_LAT, MY_LON, LATE_NIGHT_START_HOUR, world,
                                     ['EscaleraPBSensor1', 'EscaleraPBSensor2'],
                                      world.get_thing_by_name('EscaleraPB')))

    world.register_thing(ColorDimmableLamp('Belador', world.mqtt))
    world.register_thing(DimmableLamp('NicoVelador', world.mqtt))
    world.register_thing(BeladorBoton('BeladorBoton', world, scenes))
    world.register_thing(BatipiezaBoton('BatipiezaBoton', world, scenes))

    world.register_thing(DimmableLamp('Oficina', world.mqtt))

    world.register_thing(MultiThing('Comedor', ColorDimmableLamp, ['ComedorL', 'ComedorR'], world.mqtt))
    world.register_thing(DimmableLamp('Snoopy', world.mqtt))
    world.register_thing(BotonComedorHue('BotonComedor', world))

    world.register_thing(ColorDimmableLamp('OlmaVelador', world.mqtt))


