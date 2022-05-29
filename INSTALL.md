# Install instructions

This readme has been tested in a RaspberryPi 3, but it should be applicable to any Linux-y system.

Besides hardware, running BatHouse requires:

1. An mqtt broker
2. zigbee2mqtt
3. A bunch of pipenv dependencies

*Important*
Give your devices friendly names in zigbee2mqtt - otherwise BatHouse will display them by their ID.

## Mqtt server
1. Mosquitto is easiest:
$ sudo apt-get install mosquitto


## Zigbee2mqtt
### Install zigbee2mqtt / https://www.zigbee2mqtt.io/
Note: instructions here not quite the same as https://www.zigbee2mqtt.io/getting_started/running_zigbee2mqtt.html

Without a Zigbee stick plugged, in:

$ sudo apt-get install npm
$ git clone https://github.com/Koenkk/zigbee2mqtt.git
$ npm install
$ npm start

At this point it should fail with "cannot open /dev/ttyAMC0". Now plug the Zigbee stick and verify a new /dev/tty device is avaiable (may be /dev/ttyACM0, ttyUSB0 or something else). Next run of `npm start` should succeed.

### Configure zigbee2mqtt

1. zigbee2mqtt keeps device info in zigbee2mqtt/data/database.db. Backup the db file and move it around if you change zigbee2mqtt's directory.
2. Give it a test run, try out (and pair) all devices. Then edit configuration.yaml - give friendly names to all discovered devices.
3. Link zigbee2mqtt.service to /etc/systemd/system/zigbee2mqtt.service to make it a system service.
4. Usueful control commands:

 # Show status
 sudo systemctl enable zigbee2mqtt.service
 # Enable service
 systemctl status zigbee2mqtt.service
 # Start zigbee2mqtt
 $ sudo systemctl start zigbee2mqtt
 # Stopping zigbee2mqtt
 sudo systemctl stop zigbee2mqtt
 # View the log of zigbee2mqtt
 sudo journalctl -u zigbee2mqtt.service -f

### Zigbee stick crashes?
* Too many concurrent messages received by the usb stick might make it crash: https://github.com/Koenkk/zigbee2mqtt/issues/1181
	* try increasing this lib/util/zigbeeQueue.js to e.g. const delay = 500; or maxSimultaneouslyRunning = 2;
		This should reduce the traffic to the CC2531. 
	* Add to mosquitto.conf "max_inflight_messages 5" to reduce the number of concurrent messages
	* Use qos=1 when publishing messages and subscribing to topics in Mosquitto

More troubleshooting
* https://github.com/Koenkk/zigbee2mqtt/issues/156 


## Run BatHouse 

## Install dependencies

$ python3 -m pipenv install requests

Note the project has a Pipfile but no Pipfile.lock. This is because hashes for the RaspberryPi and for x86 seem to be different, making pipenv installs fail. Remember not to commit any Pipfile.lock in PR's.

## Config
Edit config.json.example with right config. Also edit and install the crontab entries as specified in the file "crontab".

## Install service:
$ cd /etc/systemd/system && sudo ln -s /home/pi/BatHouse/BatHouse.service 
$ sudo systemctl enable BatHouse

## Start and stop:
$ sudo systemctl start BatHouse
$ sudo systemctl stop BatHouse

## Status:
$ systemctl status BatHouse
$ sudo journalctl -u BatHouse -f


