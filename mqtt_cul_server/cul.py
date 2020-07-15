import sys
import logging
import os
import serial


class Cul(object):
    """Helper class to encapsulate serial communication with CUL device"""

    def __init__(self, serial_port, test=False):
        """Create instance with a given serial port"""
        if test:
            self.serial = sys.stderr
        else:
            if not os.path.exists(serial_port):
                raise ValueError("cannot find CUL device %s" % serial_port)
            try:
                self.serial = serial.Serial(
                    port=serial_port, baudrate=115200, timeout=1
                )
            except serial.SerialException as e:
                logging.error("Could not open CUL device: %s", e)

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