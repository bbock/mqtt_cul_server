#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import logging
from sys import base_prefix, prefix
import paho.mqtt.client as mqtt
from cul import Cul
from somfy_shutter import SomfyShutter
from intertechno import Intertechno


class Cul_mqtt_server:

    prefix = "homeconnect"
    components = []

    def __init__(self, cul):
        self.cul = Cul(cul)
        self.mqtt_client = mqtt.Client()

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.components.append(Intertechno(self.cul, self.prefix))
        self.components.append(SomfyShutter(self.cul, self.prefix))

        try:
            # TODO: get MQTT endpoint via config file
            self.mqtt_client.connect("localhost", 1883, 60)
        except Exception as e:
            logging.error("Could not connect to MQTT broker")
            sys.exit(1)

    def on_connect(self, _userdata, _flags, _rc):
        """The callback for when the MQTT client receives a CONNACK response"""

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.mqtt_client.subscribe(self.prefix + "/#")

    def on_message(self, _client, _userdata, msg):
        """The callback for when a message is received"""

        prefix, devicetype, component, devicename = msg.topic.split("/")

        for c in self.components:
            if component == c.get_component_name():
                c.on_message(msg)
                break

        logging.warning("component %s unknown", msg.topic)
        raise ValueError

    def listen(self):
        self.mqtt_client.loop_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control devices via CUL RF USB stick")
    parser.add_argument(
        "--cul", help="serial port with connected CUL device", required=True
    )
    parser.add_argument("--verbose", help="verbose output", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    if not os.path.exists(args.cul):
        raise ValueError("cannot find CUL device %s" % args.cul)

    cms = Cul_mqtt_server(args.cul)
    cms.listen()
