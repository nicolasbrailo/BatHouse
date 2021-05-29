#!/bin/bash

set -eu
set -o pipefail

journalctl -u mosquitto -u zigbee2mqtt -u BatHouse -u co2reader -f

