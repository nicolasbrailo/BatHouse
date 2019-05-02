#!/bin/bash

source /home/pi/kryten/env/bin/activate && \
        googlesamples-assistant-pushtotalk \
        --device-model-id shutmedown-b7af9-shutmedownthing-1e6whh \
        --project-id shutmedown-b7af9 \
        --lang es-ES --once --verbose -i /home/pi/kryten/apagar_baticueva_tv.wav

