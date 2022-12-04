from zigbee2mqtt2flask.zigbee2mqtt2flask.things import Thing

import logging
logger = logging.getLogger('zigbee2mqtt2flask.thing')

# sudo apt-get install python3-lxml libxslt1-dev
# python3 -m pipenv install soco --skip-lock
from soco import SoCo
from soco import discover

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

