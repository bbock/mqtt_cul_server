# -*- coding: utf-8 -*-
"""
Control Somfy RTS blinds via CUL RF USB stick

This module implements the serial protocol of culfw for the Somfy
wireless communication protocol.
"""

import json
import logging
import os


class SomfyShutter:
    """
    Control Somfy RTS blinds via CUL RF USB stick

    This module implements the serial protocol of culfw for the Somfy
    wireless communication protocol.
    """

    class SomfyShutterState:
        def __init__(self, statefile):
            self.statefile = statefile
            with open("state/somfy/" + statefile) as fh:
                self.state = json.loads(fh.read())

        def save(self):
            """Save state to JSON file"""
            with open("state/somfy/" + self.statefile, "w") as fh:
                json.dump(self.state, fh)

        def increase_rolling_code(self):
            """Increment rolling_code, enc_key lower 4 bit and save to statefile"""
            self.state["rolling_code"] += 1
            # check for overflow
            if self.state["rolling_code"] == 0x1000000:
                self.state["rolling_code"] = 0
            self.state["enc_key"] += 1
            if self.state["enc_key"] == 0x10:
                self.state["enc_key"] = 0x0
            self.save()

    def __init__(self, cul, mqtt_client, prefix):
        self.cul = cul
        self.prefix = prefix

        self.devices = []
        for statefile in os.listdir("state/somfy/"):
            if ".json" in statefile:
                self.devices.append(self.SomfyShutterState(statefile))

        for device in self.devices:
            # send messages for device discovery
            self.send_discovery(device, mqtt_client)

    def get_component_name(self):
        return "somfy"

    def send_discovery(self, device, mqtt_client):
        """
        Send Home Assistant - compatible discovery messages

        for more information about MQTT-discovery and MQTT switches, see
        https://www.home-assistant.io/docs/mqtt/discovery/
        https://www.home-assistant.io/integrations/cover.mqtt/

        There's no state topic, as Somfy is fire-and-forget with no
        feedback about the state.
        """

        base_path = self.prefix + "/cover/somfy/" + device.state["address"]

        configuration = {
            "~": base_path,
            "command_topic": "~/set",
            "payload_open": "OPEN",
            "payload_close": "CLOSE",
            "payload_stop": "STOP",
            "optimistic": True,
            "device_class": device.state["device_class"],
            "name": device.state["name"],
            "unique_id": "somfy_" + device.state["address"],
        }

        topic = base_path + "/config"
        mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)

    def calculate_checksum(self, command):
        """
        Calculate checksum for command string

        From https://pushstack.wordpress.com/somfy-rts-protocol/ :
        The checksum is calculated by doing a XOR of all nibbles of the frame.
        To generate a checksum for a frame set the 'cks' field to 0 before
        calculating the checksum.
        """
        cmd = bytearray(command, "utf-8")
        checksum = 0
        for char in cmd:
            checksum = checksum ^ char ^ (char >> 4)
        checksum = checksum & 0xF
        return "{:01X}".format(checksum)

    def command_string(self, command, device):
        """
        A Somfy command is a hex string of the following form: KKC0RRRRSSSSSS

        KK - Encryption key: First byte always 'A', second byte varies
        C - Command (1 = My, 2 = Up, 4 = Down, 8 = Prog)
        0 - Checksum (set to 0 for calculating checksum)
        RRRR - Rolling code
        SSSSSS - Address (= remote channel)
        """
        commands = {
            "my": 1,
            "up": 2,
            "my-up": 3,
            "down": 4,
            "my-down": 5,
            "up-down": 6,
            "my-up-down": 7,
            "prog": 8,
            "enable-sun": 9,
            "disable-sun": 10,
        }
        if command in commands:
            command_string = "A{:01X}{:01X}0{:04X}{}".format(
                device.state["enc_key"],
                commands[command],
                device.state["rolling_code"],
                device.state["address"],
            )
        else:
            raise NameError("unknown command")
        command_string = (
            command_string[:3]
            + self.calculate_checksum(command_string)
            + command_string[4:]
        )
        command_string = "Ys" + command_string + "\n"
        return command_string.encode()

    def send_command(self, command, device):
        """Send command string via CUL device"""
        command_string = self.command_string(command, device)
        logging.info("sending command string %s to %s", command_string, device.name)
        self.cul.send_command(command_string)
        device.increase_rolling_code()

    def on_message(self, message):
        prefix, devicetype, component, devicename = message.topic.split("/")
        command = str(message.payload)

        if prefix != self.prefix:
            logging.info("Ignoring message due to prefix")
            return
        if devicetype != "cover":
            raise ValueError("Somfy can only handle covers")
        if component != "somfy":
            raise ValueError("Received command for different component")

        device = None
        for d in self.devices:
            if d.state["name"] == devicename:
                device = d
                break
        if not device:
            raise ValueError("Device not found")

        if command == "OPEN":
            self.send_command("up", device)
        elif command == "CLOSE":
            self.send_command("down", device)
        elif command == "STOP":
            self.send_command("my", device)
        else:
            raise ValueError("Command %s is not supported", command)
