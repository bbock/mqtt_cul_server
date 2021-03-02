from .. import cul

class LaCrosse:
    """
    Receive Lacrosse IT+ data via CUL RF USB stick

    This module implements the serial protocol of culfw for the LaCrosse IT+
    wireless communication protocol.

    Protocol spec:
      - http://fredboboss.free.fr/articles/tx29.php?lang=en
      - https://github.com/heliflieger/a-culfw/blob/master/culfw/clib/lacrosse.c

    """

    def __init__(self, cul, mqtt_client, prefix):
        self.cul = cul

        # send messages for device discovery
        # self.send_discovery(mqtt_client)

        # enable listening for Native RF mode 1
        command_string = "Nr1\n".encode()
        self.cul.send_command(command_string)

    def get_component_name(self):
        return "lcarosse"

    def send_discovery(self, mqtt_client):
        raise NotImplementedError()

    def decode_rx_data(self, data):
        START_MARKER = slice(0, 4)
        ID           = slice(4, 6)
        TEMPERATURE  = slice(6, 9)
        HUMIDITY     = slice(9, 11)
        CRC          = slice(11, 13)

        if isinstance(data, bytes):
            data = data.decode()

        parsed_data = {}
        try:
            if data[START_MARKER] != "N019":
                raise ValueError("cant decode")
            parsed_data["id"] = (int(data[ID], base=16) & 0x3F) >> 2
            parsed_data["new_battery"] = (int(data[ID], base=16) & 0x2) >> 1
            parsed_data["temperature"] = int(data[TEMPERATURE]) / 10 - 40
            parsed_data["weak_battery"] = int(data[HUMIDITY][0], base=16) & 0x8 >> 7
            parsed_data["humidity"] = int(data[HUMIDITY], base=16) & 0x7F
            if parsed_data["humidity"] == 106:
                # 106 means no such sensor
                del parsed_data["humidity"]
        except:
            # decode error. we don't check CRC or do any error handling (yet)
            pass
        return parsed_data

    def send_command(self, command):
        """Send command string via CUL device"""


def test_decode_data():
    cul_device = cul.Cul("", test=True)
    lacrosse = LaCrosse(cul_device, None, None)
    assert lacrosse.decode_rx_data(b"N0199E6282EC7AAAA0000719199") == {
        "id": 7,
        "new_battery": 1,
        "temperature": 22.799999999999997,
        "weak_battery": 0,
        "humidity": 46,
    }
