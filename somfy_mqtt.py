#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import os
import sys
import logging
import paho.mqtt.client as mqtt
from cul import Cul
from somfy_shutter import SomfyShutter
from intertechno import Intertechno


def on_connect(client, _userdata, _flags, _rc):
    """The callback for when the MQTT client receives a CONNACK response"""
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("somfy/#")
    client.subscribe("intertechno/#")


def on_message(_client, _userdata, msg):
    """The callback for when a PUBLISH message is received"""
    devicetype, devicename = msg.topic.split("/")
    command = str(msg.payload)

    if devicetype == "somfy":
        devicehandler = SomfyShutter(devicename, cul)
    elif devicetype == "intertechno":
        devicehandler = Intertechno(devicename, cul)
    else:
        logging.warning('device %s unknown', msg.topic)
        raise ValueError

    try:
        devicehandler.send_command(command)
    except Exception as e:
        logging.warning('could not send command: %s', e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control Somfy blinds via CUL RF USB stick')
    parser.add_argument('--cul', help='serial port with connected CUL device', required=True)
    parser.add_argument('--verbose', help='verbose output', action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    if not os.path.exists(args.cul):
        raise ValueError('cannot find CUL device %s' % args.cul)

    cul = Cul(args.cul)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect("localhost", 1883, 60)
    except Exception as e:
        logging.error("Could not connect to MQTT broker")
        sys.exit(1)

    client.loop_forever()
