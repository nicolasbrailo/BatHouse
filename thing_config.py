from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing, Lamp, DimmableLamp, ColorDimmableLamp, ColorTempDimmableLamp, Button, BatteryPoweredThing

import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler

def is_it_light_outside():
    import datetime
    import astral
    from astral.sun import sun as astral_sun

    t = astral_sun(astral.Observer(51.5464371, 0.111148), date=datetime.date.today())
    tolerance = datetime.timedelta(minutes=45)
    sunrise = t['sunrise'] + tolerance
    sunset = t['sunset'] - tolerance
    ahora = datetime.datetime.now(t['sunset'].tzinfo)
    sun_out = ahora > sunrise and ahora < sunset
    return sun_out


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
        if action == 'brightness_down_click':
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


#class MultiIkeaMotionSensor(Thing):
#    class SensorImpl(BatteryPoweredThing):
#        def __init__(self, world, mqtt_id, on_occupant_entered, on_occupant_left):
#            super().__init__(mqtt_id)
#            logger.warning(f"Registering thing {mqtt_id}")
#            world.register_thing(self)
#            self.on_occupant_entered = on_occupant_entered
#            self.on_occupant_left = on_occupant_left
#            self.occupied = False
#
#        def consume_message(self, topic, msg):
#            if 'occupancy' in msg:
#                if msg['occupancy']:
#                    self.on_occupant_entered()
#                    self.occupied = True
#                else:
#                    self.on_occupant_left()
#                    self.occupied = False
#                return True
#
#            return False
#
#    def json_status(self):
#        sensor_names = [s.get_id() for s in self._sensors]
#        active = False
#        for s in self._sensors:
#            if s.occupied:
#                active = True
#        return {'sensors': sensor_names, 'active': active}
#
#    def __init__(self, world, mqtt_ids):
#        super().__init__('MultiSensor' + '_'.join(mqtt_ids))
#        self._sensors = []
#        for mqtt_id in mqtt_ids:
#            self._sensors.append(MultiIkeaMotionSensor.SensorImpl(world, mqtt_id, self._on_occupant_entered, self._on_occupant_left))
#
#        self._scheduler = BackgroundScheduler()
#        self._bg = None
#        self._scheduler.start()
#        self.timeout_secs = 60
#
#    def _on_occupant_entered(self):
#        self._maybe_cancel_timeout()
#        self._bg = self._scheduler.add_job(func=self._timeout,
#                               trigger="interval", seconds=self.timeout_secs)
#        self.activity_detected()
#
#    def _on_occupant_left(self):
#        for sensor in self._sensors:
#            if sensor.occupied:
#                return
#        # All sensors are marked as cleared
#        self._maybe_cancel_timeout()
#        self.all_vacant()
#
#    def _maybe_cancel_timeout(self):
#        if self._bg is not None:
#            self._bg.remove()
#            self._bg = None
#
#    def _timeout(self):
#        self._maybe_cancel_timeout()
#        self.activity_timeout()
#
#    def activity_detected(self):
#        pass
#
#    def all_vacant(self):
#        pass
#
#    def activity_timeout(self):
#        pass

class Foo(MultiIkeaMotionSensor):
    def __init__(self, world, mqtt_ids, light):
        super().__init__(world, mqtt_ids)
        self.light = light
        self.light_on_because_activity = False

    def activity_detected(self):
        if is_it_light_outside():
            return

        if not self.light.is_on:
            self.light_on_because_activity = True
            self.light.set_brightness(30, broadcast_update=False)
            self.light.broadcast_new_state(transition_time=3)

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
    world.register_thing(Foo(world, ['IkeaMotionSensorUpstairs','IkeaMotionSensorEntrepiso'], world.get_thing_by_name('EntrepisoLamp')))

