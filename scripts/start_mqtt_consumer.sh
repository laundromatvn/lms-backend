#!/bin/sh
uvicorn app.mqtt_consumer:app --host 0.0.0.0 --port 8001 --reload
