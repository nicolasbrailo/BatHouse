#!/bin/bash

set -eu
set -o pipefail

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


# Configure co2reader
nosu git clone git@github.com:nicolasbrailo/co2.git $BATHOME_TGTDIR/co2

ln -s $BATHOME_TGTDIR/co2/co2reader.service /etc/systemd/system
ln -s $BATHOME_TGTDIR/co2/99-co2dev.rules /etc/udev/rules.d/
service udev restart
udevadm control --reload-rules && udevadm trigger
systemctl daemon-reload
systemctl restart co2reader
systemctl status co2reader
systemctl enable co2reader


