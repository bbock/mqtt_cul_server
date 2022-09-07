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

    def crc(self, data):
        """calculate CRC-8 with poly = 0x31 """
        crc = 0
        for byte in data:
            val = byte
            for _ in range(8):
                do_xor = (crc ^ val) & 0x80
                crc = (crc << 1) & 0xff
                if do_xor:
                    crc ^= 0x31
                val = (val << 1) & 0xff
        return crc


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
                raise ValueError(f"unexpected message length {len(data)}: {data}")
            if data[START_MARKER] != "9":
                raise ValueError("cant decode: wrong start marker")
            received_crc = int(data[CRC][0]+data[CRC][1], base=16)
            calculated_crc = self.crc(bytes.fromhex(data[ALL_DATA]))
            if received_crc != calculated_crc:
                raise ValueError(f"CRC failure: received 0x{received_crc:08b}, " \
                                 f"calculated 0x{calculated_crc:08b}")
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
        except ValueError as e:
            # decode error. log problem and ignore message / data
            logging.info(f"decode error for {data}: {e}")
            parsed_data = {}
        return parsed_data

    def on_message(self, message):
        # ignore MQTT commands for lacrosse, it is RF receive-only, no commands
        pass

    def on_rf_message(self, message):
        decoded = self.decode_rx_data(message.strip())
        if "id" not in decoded:
            # message could not be decoded, ignore
            return
        if decoded["id"] not in self.devices:
            logging.info("sending discovery for %d", decoded["id"])
            self.send_discovery(decoded)
        else:
            logging.debug("known devices: %s", str(self.devices))
        topic = self.prefix + "/sensor/lacrosse/" + str(decoded["id"]) + "/state"
        del decoded["id"]
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
    good_messages = [
        "N019EC615414BAAAA0000571601",
        "N019986373FC9AAAA0000109880",
        "N019986373EF8AAAA000002B204",
        "N019986363E0CAAAA000001A4A0",
    ]
    bad_messages = [
        "N019ECE33398CAAAA0000A17C69",
    ]
    for m in good_messages:
        assert lacrosse.decode_rx_data(m)
    for m in bad_messages:
        assert not lacrosse.decode_rx_data(m)

def test_real_data():
    cul_device = cul.Cul("", test=True)
    lacrosse = LaCrosse(cul_device, None, None)
    messages = [
        "N019A86414280AAAA0000480473",
        "N019A864143B1AAAA00000B3897",
        "N019A864143B1AAAA000015DA99",
        "N019A86414280AAAA0000090092",
    ]
    for m in messages:
        logging.info(lacrosse.decode_rx_data(m))
