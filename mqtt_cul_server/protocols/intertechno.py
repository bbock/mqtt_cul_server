# -*- coding: utf-8 -*-
"""
Control Intertechno devices via CUL RF USB stick

This module implements the serial protocol of culfw for the Intertechno
wireless communication protocol.
"""

import json
import logging
import re


class Intertechno:
    """
    Control Intertechno devices via CUL RF USB stick

    This module implements the serial protocol of culfw for the Intertechno
    wireless communication protocol.
    """

    def __init__(self, cul, mqtt_client, prefix):
        self.cul = cul

        # TODO: get system ID from config file
        self.system_id = "0FF00"
        self.prefix = prefix

        # send messages for device discovery
        self.send_discovery(mqtt_client)

    def get_component_name(self):
        return "intertechno"

    def send_discovery(self, mqtt_client):
        """
        Send Home Assistant - compatible discovery messages

        for more information about MQTT-discovery and MQTT switches, see
        https://www.home-assistant.io/docs/mqtt/discovery/
        https://www.home-assistant.io/integrations/switch.mqtt/

        There's no state topic, as Intertechno is fire-and-forget with no
        feedback about the state.
        """

        # each system can have exactly these 5 units
        unit_ids = ["0FFFF", "F0FFF", "FF0FF", "FFF0F", "FFFF0"]

        configuration = {
            "device_class": "switch",
            "command_topic": "~/set",
            "payload_on": "ON",
            "payload_off": "OFF",
            "optimistic": True,
        }

        for unit_id in unit_ids:
            base_prefix = (
                self.prefix + "/switch/intertechno/" + self.system_id + unit_id
            )
            configuration["~"] = base_prefix
            configuration["name"] = "Intertechno " + self.system_id + " " + unit_id
            configuration["unique_id"] = "intertechno_" + self.system_id + unit_id

            topic = base_prefix + "/config"
            mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)

    def on_message(self, message):
        prefix, devicetype, component, devicename = message.topic.split("/")
        command = str(message.payload)

        if prefix != self.prefix:
            logging.info("Ignoring message due to prefix")
            return
        if devicetype != "switch":
            raise ValueError("Intertechno can only handle switches")
        if component != "intertechno":
            raise ValueError("Received command for different component")
        if re.match(r"^[0F]{10}$", devicename) is None:
            raise ValueError("Intertechno device name does not match [0F]{10}")

        if command == "ON":
            commandbits = "FF"
        elif command == "OFF":
            commandbits = "F0"
        else:
            raise ValueError("Command %s is not supported", command)

        if devicename[0:5] != self.system_id:
            logging.info("Received command for different Intertechno system. Ignoring.")
            return

        command = "is" + devicename + commandbits + "\n"
        self.send_command(command)

    def send_command(self, command):
        """Send command string via CUL device"""
        command_string = command.encode()
        logging.debug("sending intertechno command %s", command)
        self.cul.send_command(command_string)
