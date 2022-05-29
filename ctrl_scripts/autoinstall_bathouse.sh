#!/bin/bash

set -eu
set -o pipefail

echo "This script may be destructive if you changed your config files."
echo "Ensure you really want to run this and then delete the exit command in this script"
#exit

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


# Configure BatHouse
apt-get install python3-pip
pip3 install pipenv

# authbind -> run in port 80 with no root
apt-get install authbind
touch /etc/authbind/byport/80
chmod 777 /etc/authbind/byport/80

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
ExecStart=/usb/bin/authbind --deep /usr/bin/python3 -m pipenv run python ./server.py
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


