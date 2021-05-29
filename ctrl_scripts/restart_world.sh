#!/bin/bash

set -eu
set -o pipefail

systemctl restart zigbee2mqtt
systemctl restart mosquitto
systemctl restart co2reader

sleep 4
systemctl restart BatHouse


