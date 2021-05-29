#!/bin/bash

set -eu
set -o pipefail

systemctl restart zigbee2mqtt
systemctl restart mosquitto

sleep 4
systemctl restart BatHouse


