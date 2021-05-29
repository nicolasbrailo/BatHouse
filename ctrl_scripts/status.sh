#!/bin/bash

set -eu
set -o pipefail

systemctl status mosquitto zigbee2mqtt BatHouse

