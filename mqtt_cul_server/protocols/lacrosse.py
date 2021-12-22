import crc8
import json
import logging
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
        self.set_listening_mode()

    @classmethod
    def get_component_name(cls):
        return "lacrosse"

    def set_listening_mode(self):
        """Enable listening for Native RF mode 1"""
        command_string = "Nr1\n".encode()
        self.cul.send_command(command_string)


    def send_discovery(self, parsed_data):
        """
        Send Home Assistant - compatible discovery messages

        for more information about MQTT-discovery and MQTT switches, see
        https://www.home-assistant.io/docs/mqtt/discovery/
        https://www.home-assistant.io/integrations/sensor.mqtt/
        """
        # register id as known to not send discovery every time
        self.devices.append(parsed_data["id"])
        unit_id = str(parsed_data["id"])
        # temperature
        configuration = {
            "device_class": "temperature",
            "state_class": "measurement",
            "name": "LaCrosse " + unit_id + " Temperature",
            "unique_id": "lacrosse_" + unit_id + "_temperature",
            "unit_of_measurement": "°C",
            "state_topic": self.prefix + "/sensor/lacrosse/" + unit_id + "/state",
            "value_template": "{{value_json.temperature}}",
            "device": {
                "name": "Temperatur / Luftfeuchtesensor " + unit_id,
                "identifiers": "lacrosse_" + unit_id,
                "model": "TX29 DTH-IT",
                "manufacturer": "LaCrosse"
            },
        }
        topic = self.prefix + "/sensor/lacrosse/" + unit_id + "_temperature/config"
        self.mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)
        # humidity
        configuration = {
            "device_class": "humidity",
            "state_class": "measurement",
            "name": "LaCrosse " + unit_id + " Humidity",
            "unique_id": "lacrosse_" + unit_id + "_humidity",
            "unit_of_measurement": "%",
            "state_topic": self.prefix + "/sensor/lacrosse/" + unit_id + "/state",
            "value_template": "{{value_json.humidity}}",
            "device": {
                "name": "Temperatur / Luftfeuchtesensor " + unit_id,
                "identifiers": "lacrosse_" + unit_id,
                "model": "TX29 DTH-IT",
                "manufacturer": "LaCrosse"
            },
        }
        topic = self.prefix + "/sensor/lacrosse/" + unit_id + "_humidity/config"
        self.mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)
        # battery
        configuration = {
            "device_class": "battery",
            "name": "LaCrosse " + unit_id + " Battery",
            "unique_id": "lacrosse_" + unit_id + "_battery",
            "unit_of_measurement": "%",
            "state_topic": self.prefix + "/sensor/lacrosse/" + unit_id + "/state",
            "value_template": "{{value_json.battery}}",
            "device": {
                "name": "Temperatur / Luftfeuchtesensor " + unit_id,
                "identifiers": "lacrosse_" + unit_id,
                "model": "TX29 DTH-IT",
                "manufacturer": "LaCrosse"
            },
        }
        topic = self.prefix + "/sensor/lacrosse/" + unit_id + "_battery/config"
        self.mqtt_client.publish(topic, payload=json.dumps(configuration), retain=True)

    def decode_rx_data(self, data):
        START_MARKER = slice(3, 4)
        ID           = slice(4, 6)
        TEMPERATURE  = slice(6, 9)
        HUMIDITY     = slice(9, 11)
        ALL_DATA     = slice(3, 11)
        CRC          = slice(11, 13)

        parsed_data = {}
        try:
            if len(data) != 27:
                logging.debug("unexpected message length %d: %s", len(data), data)
            if data[START_MARKER] != "9":
                raise ValueError("cant decode: wrong start marker")
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
        except:
            # decode error. we don't check CRC or do any error handling (yet)
            logging.info("decode error: %s", data, exc_info=True)

        # CRC check, currently only logs result as some correct messages cannot
        # be successfuly validated yet.
        received_crc = int(data[CRC][1]+data[CRC][0], base=16)
        calculated_crc = crc8.crc8()
        calculated_crc.update(bytes.fromhex(data[ALL_DATA]))
        calculated_crc = int(calculated_crc.hexdigest(), base=16)
        if received_crc != calculated_crc:
            logging.debug("device %d CRC NOT ok: received: 0x%02X, calculated: 0x%02X", parsed_data["id"], received_crc, calculated_crc)
        else:
            logging.debug("device %d, CRC ok: 0x%02X", parsed_data["id"], calculated_crc)

        return parsed_data

    def on_message(self, message):
        # ignore MQTT commands for lacrosse, it is RF receive-only, no commands
        pass

    def on_rf_message(self, message):
        decoded = self.decode_rx_data(message)
        if "id" not in decoded:
            logging.info("unhandled: no ID in %s", decoded)
            return
        if decoded["id"] not in self.devices:
            logging.info("sending discovery for %d", decoded["id"])
            self.send_discovery(decoded)
        else:
            logging.info("known devices: %s", str(self.devices))
        topic = self.prefix + "/sensor/lacrosse/" + str(decoded["id"]) + "/state"
        del(decoded["id"])
        self.mqtt_client.publish(topic, payload=json.dumps(decoded), retain=False)


def test_decode_data():
    """Test LaCrosse data parsing"""
    cul_device = cul.Cul("", test=True)
    lacrosse = LaCrosse(cul_device, None, None)
    assert lacrosse.decode_rx_data("N0199E6282EC7AAAA0000719199") == {
        "id": 7,
        "battery": 100,
        "temperature": 22.8,
        "humidity": 46,
    }
    assert lacrosse.decode_rx_data("N019986373FC9AAAA0000000783") == {
        "id": 6,
        "battery": 50,
        "temperature": 23.7,
        "humidity": 63,
    }

def test_crc():
    cul_device = cul.Cul("", test=True)
    lacrosse = LaCrosse(cul_device, None, None)
    messages = [
        "N019EC615414BAAAA0000571601",
        "N019986373FC9AAAA0000109880",
        "N019986373EF8AAAA000002B204",
        "N019986363E0CAAAA000001A4A0",
    ]
    for m in messages:
        assert lacrosse.decode_rx_data(m)