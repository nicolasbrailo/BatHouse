#!/bin/bash

set -eu
set -o pipefail

echo "This script may be destructive if you changed your config files."
echo "Ensure you really want to run this and then delete the exit command in this script"
exit

NORMAL_USER="pi"
BATHOME_TGTDIR="/home/pi/BatHome"
BATHOME_LOGS="$BATHOME_TGTDIR/logs"
BATHOME_CFG="$BATHOME_TGTDIR/conf"

if [ "$EUID" -ne 0 ]; then
	echo "Please run as root"
  exit
fi

nosu() {
	sudo -H -u $NORMAL_USER bash << EOF
$@
EOF
}

nosu mkdir -p "$BATHOME_TGTDIR"
nosu mkdir -p "$BATHOME_LOGS"
nosu mkdir -p "$BATHOME_CFG"

#Xapt-get update
sudo apt-get upgrade
apt-get --assume-yes install mosquitto npm

#X# Configure mosquitto
touch $BATHOME_LOGS/mosquitto.log
chown mosquitto:mosquitto $BATHOME_LOGS/mosquitto.log
nosu ln -s /etc/mosquitto/mosquitto.conf "$BATHOME_CFG/mosquitto.conf"
sed -i "s#log_dest .*#log_dest file $BATHOME_TGTDIR/logs/mosquitto.log#" /etc/mosquitto/mosquitto.conf

systemctl daemon-reload
systemctl restart mosquitto
systemctl status mosquitto
systemctl enable mosquitto

# Configure zigbee2mqtt
nosu git clone https://github.com/Koenkk/zigbee2mqtt.git $BATHOME_TGTDIR/zigbee2mqtt
nosu npm install $BATHOME_TGTDIR/zigbee2mqtt

nosu ln -s "$BATHOME_TGTDIR/zigbee2mqtt/data/log" "$BATHOME_LOGS/zigbee2mqtt"
nosu ln -s "$BATHOME_TGTDIR/zigbee2mqtt/data/configuration.yaml" "$BATHOME_CFG/zigbee2mqtt.conf"

cat << EOF > "$BATHOME_CFG/zigbee2mqtt.conf"
homeassistant: false
permit_join: true
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost'
serial:
  disable_led: true
  port: /dev/ttyACM0
advanced:
  ikea_ota_use_test_url: true
  log_symlink_current: true

EOF

cat << EOF > "/etc/systemd/system/zigbee2mqtt.service"
[Unit]
Description=zigbee2mqtt
After=network.target

[Service]
ExecStart=/usr/bin/npm start
WorkingDirectory=$BATHOME_TGTDIR/zigbee2mqtt
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

EOF

# Manual start: nosu npm start --prefix $BATHOME_TGTDIR/zigbee2mqtt
systemctl daemon-reload
systemctl start zigbee2mqtt
systemctl status zigbee2mqtt
systemctl enable zigbee2mqtt

# Configure BatHouse
pip3 install pipenv

pushd $PWD > /dev/null
nosu git clone --recurse-submodules git@github.com:nicolasbrailo/BatHouse.git
cd $BATHOME_TGTDIR/BatHouse
nosu npm install handlebars
nosu python3 -m pipenv install requests
popd

nosu ln -s "$BATHOME_TGTDIR/BatHouse/config.json" "$BATHOME_CFG/bathouse.conf"

cat << EOF > "/etc/systemd/system/BatHouse.service"
[Unit]
Description=BatHouse
After=zigbee2mqtt.target

[Service]
ExecStart=/usr/bin/python3 -m pipenv run python ./server.py
WorkingDirectory=$BATHOME_TGTDIR/BatHouse
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target

EOF

systemctl daemon-reload
systemctl start BatHouse
systemctl status BatHouse
systemctl enable BatHouse

nosu ln -fs "$BATHOME_TGTDIR/BatHouse/ctrl_scripts/taillogs.sh" "$BATHOME_TGTDIR"
nosu ln -fs "$BATHOME_TGTDIR/BatHouse/ctrl_scripts/restart_world.sh" "$BATHOME_TGTDIR"
nosu ln -fs "$BATHOME_TGTDIR/BatHouse/ctrl_scripts/status.sh" "$BATHOME_TGTDIR"

