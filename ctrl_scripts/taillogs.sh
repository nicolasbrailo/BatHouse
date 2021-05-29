#!/bin/bash

set -eu
set -o pipefail

journalctl -u mosquitto -u zigbee2mqtt -u BatHouse -f

