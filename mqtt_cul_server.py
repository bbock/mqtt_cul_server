#!/usr/bin/env python3

import configparser
import logging

from mqtt_cul_server import MQTT_CUL_Server

if __name__ == "__main__":
    """Control devices via MQTT and CUL RF USB stick"""
    config = configparser.ConfigParser()
    config.read("mqtt_cul_server.ini")

    if config["DEFAULT"].getboolean("verbose"):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    mcs = MQTT_CUL_Server(config=config)
    mcs.start()
