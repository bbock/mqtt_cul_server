#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import os
import somfy_shutter
import cul
import paho.mqtt.client as mqtt
import logging


def on_connect(client, userdata, flags, rc):
    """The callback for when the MQTT client receives a CONNACK response"""
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("somfy/#")


def on_message(client, userdata, msg):
    """The callback for when a PUBLISH message is received"""
    device = msg.topic.split("/")[-1]
    command = str(msg.payload)

    if os.path.exists(device + '.json'):
        try:
            ss = somfy_shutter.somfy_shutter(device, cul)
            logging.info('sending command %s to shutter %s' % (command, device))
            ss.send_command(command)
        except Exception as e:
            logging.warning('could not send command: ', e)
    else:
        logging.warning('shutter %s not defined' % device)


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

    cul = cul.cul(args.cul)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect("localhost", 1883, 60)

    client.loop_forever()
