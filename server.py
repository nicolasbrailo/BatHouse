
# TODO
# * Support transition time 
#       mosquitto_pub -t "zigbee2mqtt/DeskLamp/set" -h 127.0.0.1 -m '{"state": "OFF", "transition": 5 }'
#       mosquitto_pub -t "zigbee2mqtt/DeskLamp/set" -h 127.0.0.1 -m '{"state": "ON", "brightness": "200", "transition": 10 }'
#   Transtime + set state to reduce in-fligth msgs
# * Local sensors
# * MFP integr
# * Links in app -> no redir
# * Chromecast off
# * Chromecast photo cycle
# * Cleanup js template dependencies in main app
# * Weather integration


# Read app config
import json
with open('config.json', 'r') as fp:
    CFG = json.loads(fp.read())

if CFG is None:
    raise "config.json not found"
    exit(1)


# Set up all known loggers
import logging
import logging.handlers

def configure_logger(l, verbose):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    log_fmt = '%(levelname)s - BatHome: %(message)s'
    ch.setFormatter(logging.Formatter('%(asctime)s ' + log_fmt))
    ch2 = logging.handlers.SysLogHandler(address = '/dev/log')
    ch2.setFormatter(logging.Formatter(log_fmt))

    if (logging.getLogger(l).hasHandlers()):
        logging.getLogger(l).handlers.clear()

    logging.getLogger(l).addHandler(ch)
    logging.getLogger(l).addHandler(ch2)
    logging.getLogger(l).setLevel(logging.DEBUG if verbose else logging.INFO)

    
[configure_logger(x, CFG['verbose_log']) for x in ['BatHome', 'zigbee2mqtt2flask', 'werkzeug']]


# Run as server?
if CFG["daemonize"]:
    import os
    pid = os.fork()
    if pid > 0:
        logger.info("Daemon started!")
        os._exit(0)
    logger.info("Daemon running!")


# Buid main app interface
from flask import Flask, send_from_directory
flask_app = Flask(__name__)


# Create world
from zigbee2mqtt2flask.zigbee2mqtt2flask import Zigbee2Mqtt2Flask
world = Zigbee2Mqtt2Flask(flask_app, 'ZMF', CFG["mqtt_broker_ip"], CFG["mqtt_broker_port"], 'zigbee2mqtt/')


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

world.register_thing(ColorDimmableLamp('DeskLamp', world.mqtt))
world.register_thing(DimmableLamp('Kitchen Counter - Left', world.mqtt))
world.register_thing(DimmableLamp('Kitchen Counter - Right', world.mqtt))
world.register_thing(DimmableLamp('Floorlamp', world.mqtt))
world.register_thing(DimmableLamp('Livingroom Lamp', world.mqtt))
world.register_thing(HueButton(   'HueButton', world, scenes))
world.register_thing(MyIkeaButton('IkeaButton', world))


# Register known things which are not mqtt
from thing_spotify import ThingSpotify
spotify_control = ThingSpotify(CFG, "ZMF")
world.register_thing(spotify_control)

from thing_chromecast import ThingChromecast
ThingChromecast.set_flask_bindings(flask_app, world)
if "chromecast_debug_device" in CFG and CFG["chromecast_debug_device"] != "":
    world.register_thing(ThingChromecast.mk_from_ip(CFG["chromecast_debug_device"]))
if CFG["chromecast_scan_on_startup"]:
    ThingChromecast.scan_chromecasts_and_register(world)


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
flask_socketio.run(flask_app, host=CFG['api_listen_host'], port=CFG['api_listen_port'], debug=False)
world.stop_mqtt_connection()
spotify_control.shutdown()

