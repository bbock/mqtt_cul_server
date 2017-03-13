#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys
import serial


class cul:
    """Helper class to encapsulate serial communication with CUL device"""

    serial = ""

    def __init__(self, serial_port):
        """Create instance with a given serial port"""
        try:
            self.serial = serial.Serial(port=serial_port, baudrate=115200, timeout=1)
        except Exception as e:
            print("Could not open CUL device", e)
            sys.exit(1)

    def get_cul_version(self):
        """Get CUL version"""
        self.serial.write("V\n")
        self.serial.flush()
        version = self.serial.readline()
        print(version)

    def send_command(self, command_string):
        """Send command string to serial port with CUL device"""
        try:
            self.serial.write(command_string)
            self.serial.flush()
        except Exception as e:
            print("Could not send command to shutter", e)
            sys.exit(1)
