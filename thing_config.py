from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing, Lamp, DimmableLamp, ColorDimmableLamp, ColorTempDimmableLamp, Button, MultiIkeaMotionSensor

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
            self.world.get_thing_by_name('Spotify').volume_up()
            return True
        if action == 'brightness_down_click':
            self.world.get_thing_by_name('Spotify').volume_down()
            return True
        if action == 'toggle':
            self.world.get_thing_by_name('Spotify').playpause()
            return True
        if action == 'arrow_right_click':
            self.world.get_thing_by_name('Spotify').play_next_in_queue()
            return True
        if action == 'arrow_left_click':
            self.world.get_thing_by_name('Spotify').play_prev_in_queue()
            return True

        logger.warning("Unknown action: Ikea button - ", action)


class MotionActivatedLight(MultiIkeaMotionSensor):
    def __init__(self, world, sensor_mqtt_ids, light):
        super().__init__(world, sensor_mqtt_ids)
        self.light = light
        self.light_on_because_activity = False

    def activity_detected(self):
        if is_it_light_outside():
            return

        if not self.light.is_on:
            brightness = 5 if is_it_late_night() else 50
            self.light_on_because_activity = True
            self.light.set_brightness(brightness)

    def all_vacant(self):
        if self.light_on_because_activity:
            self.light.light_off()

    def activity_timeout(self):
        self.all_vacant()


def register_all_things(world, scenes):
    world.register_thing(ColorDimmableLamp('BaticomedorLamp', world.mqtt))
    world.register_thing(ColorDimmableLamp('EmliviaRoomLamp', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('EntrepisoLamp', world.mqtt))
    world.register_thing(DimmableLamp('BatiofficeDeskLamp', world.mqtt))
    world.register_thing(DimmableLamp('BatBedsideLamp', world.mqtt))
    world.register_thing(IkeaButton('BotonIkeaBelen', world, scenes))
    world.register_thing(IkeaButton2('BotonIkeaComedor', world, scenes))
    world.register_thing(ColorTempDimmableLamp('KitchenLamp', world.mqtt))
    world.register_thing(ColorTempDimmableLamp('BanioLamp', world.mqtt))
    world.register_thing(MotionActivatedLight(world, ['IkeaMotionSensorUpstairs','IkeaMotionSensorEntrepiso'], world.get_thing_by_name('EntrepisoLamp')))

