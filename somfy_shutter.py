# -*- coding: utf-8 -*-
"""
Control Somfy RTS blinds via CUL RF USB stick

This module implements the serial protocol of culfw for the Somfy
wireless communication protocol.
"""

import json
import logging


class somfy_shutter:
    """
    Control Somfy RTS blinds via CUL RF USB stick

    This module implements the serial protocol of culfw for the Somfy
    wireless communication protocol.
    """

    name = ""
    config = {}
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
        "disable-sun": 10
    }
    cul = ""

    def __init__(self, shutter, cul):
        """Create instance with a given shutter name"""
        try:
            configfile = open(str(shutter) + ".json")
            config = json.loads(configfile.read())
        except Exception as e:
            print("Could not load config from file for device", shutter, e)
        self.name = shutter
        self.config = config
        self.cul = cul

    def calculate_checksum(self, command):
        """
        Calculate checksum for command string

        From https://pushstack.wordpress.com/somfy-rts-protocol/ :
        The checksum is calculated by doing a XOR of all nibbles of the frame.
        To generate a checksum for a frame set the 'cks' field to 0 before
        calculating the checksum.
        """
        cmd = bytearray(command, 'utf-8')
        checksum = 0
        for char in cmd:
            checksum = checksum ^ char ^ (char >> 4)
        checksum = checksum & 0xf
        return("{:01X}".format(checksum))

    def command_string(self, command):
        """
        A Somfy command is a hex string of the following form: KKC0RRRRSSSSSS

        KK - Encryption key: First byte always 'A', second byte varies
        C - Command (1 = My, 2 = Up, 4 = Down, 8 = Prog)
        0 - Checksum (set to 0 for calculating checksum)
        RRRR - Rolling code
        SSSSSS - Address (= remote channel)
        """
        if command in self.commands:
            command_string = "A{:01X}{:01X}0{:04X}{}".format(
                self.config['enc_key'],
                self.commands[command],
                self.config['rolling_code'],
                self.config['address'])
        else:
            raise NameError('unknown command')
        command_string = command_string[:3] + self.calculate_checksum(command_string) + command_string[4:]
        command_string = "Ys" + command_string + "\n"
        return command_string.encode()

    def increase_rolling_code(self):
        """Increment rolling_code, enc_key lower 4 bit and save to config"""
        self.config['rolling_code'] += 1
        # check for overflow
        if self.config['rolling_code'] == 0x1000000:
            self.config['rolling_code'] = 0
        self.config['enc_key'] += 1
        if self.config['enc_key'] == 0x10:
            self.config['enc_key'] = 0x0

        # TODO extract save to config
        try:
            configfile = open(self.name + ".json", "w")
            json.dump(self.config, configfile)
        except Exception as e:
            print("Could not save config to file for device", self.name, e)

    def send_command(self, command):
        """Send command string via CUL device"""
        command_string = self.command_string(command)
        logging.info("sending command string ", command_string)
        self.cul.send_command(command_string)
        self.increase_rolling_code()
