# TODO
# * Baby-debounce for UI
# * Cast local file/video

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


[configure_logger(x, CFG['verbose_log']) for x in ['BatHome', 'zigbee2mqtt2flask']]
logging.getLogger('werkzeug').propagate = False


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


# Register known things in the world
from thing_config import register_all_things
register_all_things(world, scenes, flask_app)



# Register known things which are not mqtt
from thing_spotify import ThingSpotify
if 'spotify' in CFG:
    spotify_control = ThingSpotify(CFG['spotify'], "ZMF")
    world.register_thing(spotify_control)


from thing_sonos import Sonos
world.register_thing(Sonos())


from thing_chromecast import ThingChromecast
ThingChromecast.set_flask_bindings(flask_app, world)
if "chromecast_debug_device" in CFG and CFG["chromecast_debug_device"] != "":
    world.register_thing(ThingChromecast.mk_from_ip(CFG["chromecast_debug_device"]))
if CFG["chromecast_scan_on_startup"]:
    ThingChromecast.scan_chromecasts_and_register(world)



# Slideshow object
if 'pcloud' in CFG:
    from pCloud2Flask import build_pcloud_and_register_to_flask
    pcloud_cli = build_pcloud_and_register_to_flask(flask_app, '/pcloud', CFG['pcloud'])

    from ChromecastSlideshow import build_slideshow_and_register_to_flask
    build_slideshow_and_register_to_flask(flask_app, '/slideshow', pcloud_cli, world, 'Baticomedor TV')


if 'mfp' in CFG:
    # MFP integration
    from mfp import MFP_Crawler
    mfp = MFP_Crawler(flask_app,
                      CFG['mfp']['cache_file'], 
                      CFG['mfp']['user'], CFG['mfp']['pass'],
                      int(CFG['mfp']['history_days']))

if 'weather' in CFG:
    from weather_adapter import register_flask as warf
    warf(flask_app, CFG['weather'])

@flask_app.route('/shutdown_baticueva_tv')
def flask_endpoint_shutdown_baticueva_tv():
    from scenes import shutdown_baticueva_tv
    shutdown_baticueva_tv()
    return "OK"


# Set webapp path
from flask import redirect, url_for

@flask_app.route('/')
def flask_endpoint_default_redir():
    return redirect('/webapp/index.html')

@flask_app.route('/webapp/<path:urlpath>')
def flask_webapp_root(urlpath):
    return send_from_directory('./webapp/', urlpath)

# Start world interaction, wait for interrupt
flask_debug_mode = CFG['flask_debug_mode'] if 'flask_debug_mode' in CFG else False
world.start_mqtt_connection()
flask_socketio.run(flask_app, host=CFG['api_listen_host'], port=CFG['api_listen_port'], debug=flask_debug_mode)
world.stop_mqtt_connection()
spotify_control.shutdown()
slideshow.shutdown()


