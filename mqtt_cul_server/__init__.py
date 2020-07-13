import sys
import logging
import paho.mqtt.client as mqtt
from . import cul
from .protocols import somfy_shutter, intertechno


class MQTT_CUL_Server:
    components = []

    def __init__(
        self,
        cul_port="/dev/ttyACM0",
        mqtt_host="127.0.0.1",
        mqtt_port=1883,
        prefix="homeassistant",
    ):
        self.cul = cul.Cul(cul_port)
        self.mqtt_client = mqtt.Client()
        self.prefix = prefix

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        self.components.append(intertechno.Intertechno(self.cul, self.mqtt_client, prefix))
        self.components.append(somfy_shutter.SomfyShutter(self.cul, self.mqtt_client, prefix))

        try:
            self.mqtt_client.connect(mqtt_host, mqtt_port, keepalive=60)
        except Exception as e:
            logging.error("Could not connect to MQTT broker", e)
            sys.exit(1)

    def on_connect(self, mqtt_client, _userdata, _flags, _rc):
        """The callback for when the MQTT client receives a CONNACK response"""

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        mqtt_client.subscribe(self.prefix + "/#")

    def on_message(self, _client, _userdata, msg):
        """The callback for when a message is received"""

        prefix, devicetype, component, devicename = msg.topic.split("/")

        for c in self.components:
            if component == c.get_component_name():
                c.on_message(msg)
                break

        logging.warning("component %s unknown", msg.topic)
        raise ValueError

    def listen(self):
        self.mqtt_client.loop_forever()
