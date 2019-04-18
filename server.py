#import os
#pid = os.fork()
#if pid > 0:
#    print("Daemon started!")
#    os._exit(0)
#
#print("Daemon running!")

# TODO
# * Local sensors
# * Spotify tok refresh
# * MFP integr
# * Chromecast off
# * Remove duplicated name and id
# * MK proper logger for sys srvc
# * Integrate as service + parseargs
# * Cleanup js template dependencies in main app

# Buid main app interface
from flask import Flask, send_from_directory
flask_app = Flask(__name__)


# Create world
from zigbee2mqtt2flask.zigbee2mqtt2flask import Zigbee2Mqtt2Flask
world = Zigbee2Mqtt2Flask(flask_app, 'ZMF', '192.168.2.100', 1883, 'zigbee2mqtt/')


# Add websocket to main interface, let world stream messages via websockets
from flask_socketio import SocketIO
from zigbee2mqtt2flask.zigbee2mqtt2flask.mqtt_web_socket_streamer import MqttToWebSocket
flask_socketio = SocketIO(flask_app)
MqttToWebSocket.build_and_register(flask_socketio, world)


# Add preset scenes to app
from scenes import SceneHandler
scenes = SceneHandler(flask_app, world)


# Register known things in ithe world
from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing, Lamp, DimmableLamp, ColorDimmableLamp, Button
from button_config import HueButton, MyIkeaButton

world.register_thing(ColorDimmableLamp('DeskLamp', 'DeskLamp', world.mqtt))
world.register_thing(DimmableLamp('Kitchen Counter - Left', 'Kitchen Counter - Left', world.mqtt))
world.register_thing(DimmableLamp('Kitchen Counter - Right', 'Kitchen Counter - Right', world.mqtt))
world.register_thing(DimmableLamp('Floorlamp', 'Floorlamp', world.mqtt))
world.register_thing(DimmableLamp('Livingroom Lamp', 'Livingroom Lamp', world.mqtt))
world.register_thing(HueButton(   'HueButton', 'HueButton'))
world.register_thing(MyIkeaButton('IkeaButton', 'IkeaButton',
                                           world.get_thing_by_name('Kitchen Counter - Left'),
                                           world.get_thing_by_name('Kitchen Counter - Right')))

# Register known things which are not mqtt
from thing_spotify import ThingSpotify
import json
with open('config.json', 'r') as fp:
    cfg = json.loads(fp.read())
world.register_thing(ThingSpotify(cfg, "ZMF"))

from thing_chromecast import ThingChromecast
ThingChromecast.set_flask_bindings(flask_app, world)
# TODO: Replace hardcoded by always scan
# ThingChromecast.scan_chromecasts_and_register(world)
for cc in ThingChromecast.scan_network('192.168.2.101'):
    world.register_thing(cc)


# Set webapp path
from flask import redirect, url_for

@flask_app.route('/')
def flask_endpoint_default_redir():
    return redirect('/webapp/index.html')

@flask_app.route('/webapp/<path:urlpath>')
def flask_webapp_root(urlpath):
    return send_from_directory('./webapp/', urlpath)


# Start world interaction, wait for interrupt
world.start_mqtt_connection()
flask_socketio.run(flask_app, host='0.0.0.0', port=2000, debug=False)
world.stop_mqtt_connection()

