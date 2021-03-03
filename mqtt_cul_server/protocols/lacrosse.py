import json
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
        self.prefix = prefix
        self.mqtt_client = mqtt_client
        self.devices = []

        # send messages for device discovery
        # self.send_discovery(mqtt_client)

        # enable listening for Native RF mode 1
        command_string = "Nr1\n".encode()
        self.cul.send_command(command_string)

    @classmethod
    def get_component_name(cls):
        return "lacrosse"

    def send_discovery(self, parsed_data):
        """
        Send Home Assistant - compatible discovery messages

        for more information about MQTT-discovery and MQTT switches, see
        https://www.home-assistant.io/docs/mqtt/discovery/
        https://www.home-assistant.io/integrations/sensor.mqtt/
        """
        unit_id = parsed_data["id"]
        # temperature
        configuration = {
            "~": self.prefix + "/sensor/lacrosse/" + unit_id + "_temperature",
            "device_class": "temperature",
            "name": "LaCrosse " + unit_id + " temperature",
            "unique_id": "lacrosse_" + unit_id + "_temperature",
            "unit_of_measurement": "°C",
            "state_topic": self.prefix + "/sensor/lacrosse/" + unit_id + "/state",
            "value_template": "{{value_json.temperature}}",
            "battery_level_template": "{{value_json.battery}}",
        }
        topic = self.prefix + "/sensor/lacrosse/" + parsed_data["id"] + "_temperature/config"
        self.mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)
        # humidity
        configuration = {
            "~": self.prefix + "/sensor/lacrosse/" + unit_id + "_humidity",
            "device_class": "humidity",
            "name": "LaCrosse " + unit_id + " humidity",
            "unique_id": "lacrosse_" + unit_id + "_humidity",
            "unit_of_measurement": "%",
            "state_topic": self.prefix + "/sensor/lacrosse/" + unit_id + "/state",
            "value_template": "{{value_json.humidity}}",
            "battery_level_template": "{{value_json.battery}}",
        }
        topic = self.prefix + "/sensor/lacrosse/" + parsed_data["id"] + "_humidity/config"
        self.mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)

        # register id as known to not send discovery every time
        self.devices.append()

    def decode_rx_data(self, data):
        START_MARKER = slice(3, 4)
        ID           = slice(4, 6)
        TEMPERATURE  = slice(6, 9)
        HUMIDITY     = slice(9, 11)
        CRC          = slice(11, 13)

        parsed_data = {}
        try:
            if data[START_MARKER] != "9":
                raise ValueError("cant decode")
            parsed_data["id"] = (int(data[ID], base=16) & 0x3F) >> 2
            parsed_data["temperature"] = round(int(data[TEMPERATURE]) / 10 - 40, 1)
            parsed_data["humidity"] = int(data[HUMIDITY], base=16) & 0x7F
            if parsed_data["humidity"] == 106:
                # 106 means no such sensor
                del parsed_data["humidity"]
            new_battery = (int(data[ID], base=16) & 0x2) >> 1
            weak_battery = int(data[HUMIDITY][0], base=16) & 0x8 >> 7
            if weak_battery:
                parsed_data["battery"] = 10
            elif new_battery:
                parsed_data["battery"] = 100
            else:
                parsed_data["battery"] = 50
            if parsed_data["id"] not in self.devices:
                self.send_discovery(parsed_data)
        except:
            # decode error. we don't check CRC or do any error handling (yet)
            pass
        return parsed_data

    def on_message(self, message):
        # we ignore MQTT commands for lacrosse, it is receive-only
        pass

    def on_rf_message(self, message):
        decoded = self.decode_rx_data(message)
        topic = self.prefix + "/sensor/lacrosse/" + str(decoded["id"]) + "/state"
        if decoded["id"] not in self.devices:
            self.send_discovery(decoded)
        del(decoded["id"])
        self.mqtt_client.publish(topic, payload=json.dumps(decoded), retain=True)


def test_decode_data():
    """Test LaCrosse data parsing"""
    cul_device = cul.Cul("", test=True)
    lacrosse = LaCrosse(cul_device, None, None)
    print(lacrosse.decode_rx_data("N0199E6282EC7AAAA0000719199"))
    assert lacrosse.decode_rx_data("N0199E6282EC7AAAA0000719199") == {
        "id": 7,
        "battery": 100,
        "temperature": 22.799999999999997,
        "humidity": 46,
    }
