#!/usr/bin/env python3

import configparser
import logging
import os

from mqtt_cul_server import MQTT_CUL_Server

if __name__ == "__main__":
    """Control devices via MQTT and CUL RF USB stick"""
    config = configparser.ConfigParser()
    config.read("mqtt_cul_server.ini")

    if config["DEFAULT"].getboolean("verbose"):
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

    if not os.path.exists(config["DEFAULT"]["CUL"]):
        raise ValueError("cannot find CUL device %s" % config["DEFAULT"]["CUL"])

    cms = MQTT_CUL_Server(
        cul_port=config["DEFAULT"]["CUL"],
        mqtt_host=config["mqtt"]["host"],
        mqtt_port=int(config["mqtt"]["port"]),
        prefix=config["DEFAULT"]["prefix"],
    )

    cms.listen()
