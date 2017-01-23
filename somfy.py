#!/usr/bin/env python2
"""
Control Somfy RTS blinds via CUL RF USB stick

Script to control somfy blinds.
Inline configuration, as it is just for me
"""

import argparse
import json
import sys
import serial


class somfyShutter:

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
    serial = 0

    def __init__(self, shutter, cul):
        """Create instance with a given shutter name and CUL serial port"""
        try:
            self.serial = serial.Serial(port=cul, baudrate=115200, timeout=1)
            # self.serial = open(cul)
        except Exception as e:
            print("Could not open CUL device", e)
        try:
            configfile = open(str(shutter) + ".json")
            config = json.loads(configfile.read())
        except Exception as e:
            print("Could not load config from file for device", shutter, e)
        self.name = shutter
        self.config = config

    def command_string(self, command):
        """
        A Somfy command is a hex string of the following form: KKC0RRRRAAAAAA

        KK - Encryption key
        C - Command (1 = My, 2 = Up, 4 = Down, 8 = Prog)
        0 - Checksum (set to 0, is calculated automatically)
        RRRR - Rolling code
        AAAAAA - Address (= remote channel)
        """
        if command in self.commands:
            return("Ys{:02x}{:01x}0{:04x}{:06x}".format(self.config['enc_key'],
                                                      self.commands[command],
                                                      self.config['rolling_code'],
                                                      self.config['address']))
        else:
            raise NameError('unknown command')

    def increase_rolling_code(self):
        """Increment rolling_code, enc_key lower 4 bit and save to config"""
        self.config['rolling_code'] += 1
        # check for overflow
        if self.config['rolling_code'] == 0x1000000:
            self.config['rolling_code'] = 0
        self.config['enc_key'] += 1
        if self.config['enc_key'] == 0xB0:
            self.config['enc_key'] = 0xA0
        try:
            configfile = open(self.name + ".json", "w")
            json.dump(self.config, configfile)
        except Exception as e:
            print("Could not save config to file for device", self.name, e)

    def send_command(self, command):
        """Send command string to serial port with CUL device"""
        try:
            print(self.command_string(command))
            self.serial.write(command.encode())
        except Exception as e:
            print("Could not send command to shutter", e)
            sys.exit(1)
        self.increase_rolling_code()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control Somfy blinds via CUL RF USB stick')
    parser.add_argument('--cul', help='serial port with connected CUL device', required=True)
    parser.add_argument('--shutter', help='shutter to control', required=True)
    parser.add_argument('--command', help='command to send', required=True)
    args = parser.parse_args()

    # TODO: sanitization of filename
    ss = somfyShutter(shutter=args.shutter, cul=args.cul)

    ss.send_command(args.command)
