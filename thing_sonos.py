from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing

import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')

# sudo apt-get install python3-lxml libxslt1-dev
# python3 -m pipenv install soco --skip-lock
from soco import SoCo
from soco import discover
import time

def get_sonos_by_name():
    all_sonos = {}
    for x in discover():
        all_sonos[x.player_name] = x
    return all_sonos

class Sonos(Thing):
    def __init__(self):
        super().__init__("Sonos")

    def supported_actions(self):
        return ['stop']

    def json_status(self):
        return {}

    def stop(self):
        all_devs = get_sonos_by_name()
        for name in all_devs:
            logger.info(f"Stopping {name}")
            try:
                all_devs[name].pause()
            except Exception as ex:
                logger.warning(f"Failed to stop {name}: {ex}")

    def play_announcement(self, uri, force=[]):
        ANNOUNCEMENT_VOL = 50
        MAX_PLAY_WAIT_SEC = 10

        vols_to_restore = {}
        all_devs = get_sonos_by_name()

        for name in all_devs:
            try:
                something_playing = False
                if name not in force:
                    play_state = all_devs[name].get_current_transport_info()['current_transport_state']
                    something_playing = all_devs[name].is_playing_tv or \
                                            all_devs[name].is_playing_line_in or \
                                            all_devs[name].is_playing_radio or \
                                            'playing' in play_state.lower()

                if something_playing:
                    logger.info(f"Skip announcement on {name}, something else is playing")
                    continue

                vols_to_restore[name] = all_devs[name].volume
                all_devs[name].volume = ANNOUNCEMENT_VOL
                all_devs[name].play_uri(uri, title='Baticasa Announcement')
                logger.info(f"Playing {uri} in {name}, volume {all_devs[name].volume}")
            except Exception as ex:
                logger.info(f"Failed to stop {name}: {ex}")

        for name in vols_to_restore:
            timeout = MAX_PLAY_WAIT_SEC
            while True:
                play_state = all_devs[name].get_current_transport_info()['current_transport_state']
                if 'playing' not in play_state.lower() or timeout <= 0:
                    logger.info(f"Restore {name} volume to {vols_to_restore[name]}")
                    all_devs[name].volume = vols_to_restore[name]
                    break
                logger.info(f"{name} still playing, waiting...")
                timeout -= 1
                time.sleep(1)

