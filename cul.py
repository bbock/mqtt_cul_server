#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Helper class to encapsulate serial communication with CUL device"""

import sys
import logging
import serial


class Cul(object):
    """Helper class to encapsulate serial communication with CUL device"""

    serial = ""

    def __init__(self, serial_port):
        """Create instance with a given serial port"""
        try:
            self.serial = serial.Serial(port=serial_port, baudrate=115200, timeout=1)
        except serial.SerialException as e:
            logging.error("Could not open CUL device %s", e)
            sys.exit(1)

    def get_cul_version(self):
        """Get CUL version"""
        self.serial.write("V\n")
        self.serial.flush()
        version = self.serial.readline()
        return version

    def send_command(self, command_string):
        """Send command string to serial port with CUL device"""
        try:
            self.serial.write(command_string)
            self.serial.flush()
        except serial.SerialException as e:
            logging.error("Could not send command to CUL device %s", e)
            sys.exit(1)
