from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing, MultiThing, Lamp, DimmableLamp, ColorDimmableLamp, ColorTempDimmableLamp, Button, MultiIkeaMotionSensor

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from astral.sun import sun as astral_sun
import astral
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
    t = astral_sun(astral.Observer(MY_LAT, MY_LON), date=datetime.date.today())
    tolerance = datetime.timedelta(minutes=45)
    sunrise = t['sunrise'] + tolerance
    sunset = t['sunset'] - tolerance
    ahora = datetime.datetime.now(t['sunset'].tzinfo)
    sun_out = ahora > sunrise and ahora < sunset
    return sun_out

def is_it_late_night():
    t = astral_sun(astral.Observer(MY_LAT, MY_LON), date=datetime.date.today())
    sunset = t['dusk']
    next_sunrise = t['sunrise'] + datetime.timedelta(hours=24)
    ahora = datetime.datetime.now(t['sunset'].tzinfo)
    if ahora < sunset:
        return False
    if ahora > sunset and ahora < next_sunrise:
        local_hour = datetime.datetime.now().hour # no tz, just local hour
        if local_hour >= LATE_NIGHT_START_HOUR or local_hour <= next_sunrise.hour:
            return True
    return False


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
            if self.world.get_thing_by_name('BaticomedorLamp').is_on or \
                    self.world.get_thing_by_name('BaticomedorSnoopyLamp').is_on or \
                    self.world.get_thing_by_name('BatipiezaLamp').is_on or \
                    self.world.get_thing_by_name('BanioLamp').is_on or \
                    self.world.get_thing_by_name('KitchenStandLamp').is_on or \
                    self.world.get_thing_by_name('EntrepisoLamp').is_on:
                time.sleep(2)
                self.scenes.all_lights_off(all_except=['EmliviaStandLamp'])
            else:
                self.world.get_thing_by_name('BaticomedorLamp').set_brightness(10)
                self.world.get_thing_by_name('EntrepisoLamp').set_brightness(10)
            return True
        return False

class BaticomedorBoton(Button):
    def __init__(self, mqtt_id, world, scenes):
        super().__init__(mqtt_id)
        self.world = world
        self.scenes = scenes

    def handle_action(self, action, msg):
        if action == 'on-press':
            if self.world.get_thing_by_name('BaticomedorLamp').is_on:
                self.world.get_thing_by_name('BaticomedorLamp').light_off()
                self.world.get_thing_by_name('BaticomedorSnoopyLamp').light_off()
            else:
                self.world.get_thing_by_name('BaticomedorLamp').set_brightness(100)
                self.world.get_thing_by_name('BaticomedorSnoopyLamp').set_brightness(50)
            return True
        if action == 'off-press':
            if self.world.get_thing_by_name('KitchenStandLamp').is_on:
                self.world.get_thing_by_name('KitchenStandLamp').light_off()
                self.world.get_thing_by_name('KitchenSpot1').light_off()
            else:
                self.world.get_thing_by_name('KitchenStandLamp').set_brightness(100)
                self.world.get_thing_by_name('KitchenSpot1').set_brightness(100)
            return True
        if action == 'up-press':
            self.world.get_thing_by_name('BaticomedorLamp').light_off()
            self.world.get_thing_by_name('NicofficeDeskLamp').light_off()
            self.world.get_thing_by_name('NicofficeStandLamp').light_off()
            self.world.get_thing_by_name('KitchenStandLamp').light_off()
            self.world.get_thing_by_name('KitchenSpot1').light_off()
            self.world.get_thing_by_name('BaticomedorSnoopyLamp').light_off()
            self.world.get_thing_by_name('BatipiezaLamp').set_brightness(20)
            return True
        if action == 'down-press':
            return True
        if action == 'on-hold':
            return True
        if action == 'on-hold-release':
            return True
        if action == 'off-hold':
            return True
        if action == 'off-hold-release':
            return True
        if action == 'up-hold':
            return True
        if action == 'up-hold-release':
            return True
        if action == 'down-hold':
            return True
        if action == 'down-hold-release':
            return True

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


class MotionActivatedLight(MultiIkeaMotionSensor):
    def __init__(self, world, sensor_mqtt_ids, light):
        super().__init__(world, sensor_mqtt_ids)
        self.light = light
        self.light_on_because_activity = False

    def activity_detected(self):
        if is_it_light_outside():
            return

        # Only trigger if the light wasn't on before (eg manually)
        if self.light.is_on:
            return

        logger.info("MotionActivatedLight on activity_detected")
        brightness = 5 if is_it_late_night() else 50
        self.light_on_because_activity = True
        self.light.set_brightness(brightness)

    def all_vacant(self):
        logger.info("MotionActivatedLight on all_vacant")
        if self.light_on_because_activity:
            self.light_on_because_activity = False
            self.light.light_off()

    def activity_timeout(self):
        logger.info("MotionActivatedLight on timeout")
        self.all_vacant()


class MotionActivatedLightLongTimeout(MotionActivatedLight):
    def __init__(self, world, sensor_mqtt_ids, light):
        super().__init__(world, sensor_mqtt_ids, light)

    def activity_detected(self):
        # Timeout larger than sensor report time, so it will only turn off once
        # the sensor reports empty
        self.timeout_secs = 150
        super().activity_detected()

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
        light = self.world.get_thing_by_name('EmliviaStandLamp')

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

    world.register_thing(ColorTempDimmableLamp('BaticomedorLamp', world.mqtt))
    world.register_thing(DimmableLamp('BaticomedorSnoopyLamp', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('BaticomedorSpot', world.mqtt))
    world.register_thing(BaticomedorBoton('BaticomedorBoton', world, scenes))

    world.register_thing(DimmableLamp('BatipiezaLamp', world.mqtt))
    world.register_thing(BatipiezaBoton('BatipiezaBoton', world, scenes))

    world.register_thing(ColorDimmableLamp('EmliviaStandLamp', world.mqtt))
    world.register_thing(ColorDimmableLamp('EmliviaLamp', world.mqtt))

    world.register_thing(MultiThing([DimmableLamp('NicofficeDeskLamp', world.mqtt),
                                    DimmableLamp('NicofficeStandLamp', world.mqtt)]))
    world.register_thing(ColorTempDimmableLamp('NicofficeSpotLamp', world.mqtt))
    world.register_thing(NicofficeBoton('NicofficeBoton', world, scenes))

    world.register_thing(ColorTempDimmableLamp('KitchenStandLamp', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('KitchenSpot1', world.mqtt))
    world.register_thing(KitchenBoton('KitchenBoton', world, scenes))

    world.register_thing(ColorDimmableLamp('EntrepisoLamp', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('BanioLamp', world.mqtt))
    world.register_thing(MotionActivatedLightLongTimeout(world, ['IkeaMotionSensorUpstairs','IkeaMotionSensorEntrepiso'], world.get_thing_by_name('EntrepisoLamp')))
    world.register_thing(MotionActivatedLightLongTimeout(world, ['IkeaMotionSensorBanio'], world.get_thing_by_name('BanioLamp')))

