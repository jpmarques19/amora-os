#!/bin/bash
source /home/joao/Downloads/amora-os/.venv/bin/activate
PYTHONUNBUFFERED=1 python -m test_app.mqtt_test.run client --config /home/joao/Downloads/amora-os/sdk/credentials_configs.txt
