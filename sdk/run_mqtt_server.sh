#!/bin/bash
source /home/joao/Downloads/amora-os/.venv/bin/activate
PYTHONUNBUFFERED=1 python -m test_app.mqtt_test.run server --config /home/joao/Downloads/amora-os/sdk/credentials_configs.txt 2>&1 | tee mqtt_server_output.log
