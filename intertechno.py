# -*- coding: utf-8 -*-
"""
Control Intertechno devices via CUL RF USB stick

This module implements the serial protocol of culfw for the Intertechno
wireless communication protocol.
"""

import logging


class Intertechno(object):
    """
    Control Intertechno devices via CUL RF USB stick

    This module implements the serial protocol of culfw for the Intertechno
    wireless communication protocol.
    """

    cul = ""

    def __init__(self, address, cul):
        """Create instance with a given shutter name"""
        self.address = str.upper(address)
        self.cul = cul

    def command_string(self, command):
        """Generate CUL command string for Intertechno"""
        if command == "ON":
            commandbits = "FF"
        elif command == "OFF":
            commandbits = "0F"
        else:
            raise ValueError("Command %s is not supported", command)
        command_string = "is" + self.address + commandbits + "\n"
        return command_string.encode()

    def send_command(self, command):
        """Send command string via CUL device"""
        command_string = self.command_string(command)
        logging.info("sending command string %s to %s", command_string, self.address)
        self.cul.send_command(command_string)
