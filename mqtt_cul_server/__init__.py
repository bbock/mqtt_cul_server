import sys
import logging
import paho.mqtt.client as mqtt
from . import cul
from .protocols import somfy_shutter, intertechno


class MQTT_CUL_Server:
    components = []

    def __init__(self, config={}):
        self.cul = cul.Cul(config["DEFAULT"]["CUL"])
        self.mqtt_client = self.get_mqtt_client(config["mqtt"])

        # prefix for all MQTT topics
        self.prefix = config["DEFAULT"]["prefix"]

        if config["intertechno"].getboolean("enabled"):
            self.components.append(
                intertechno.Intertechno(self.cul, self.mqtt_client, self.prefix, config["intertechno"])
            )
        if config["somfy"].getboolean("enabled"):
            self.components.append(
                somfy_shutter.SomfyShutter(self.cul, self.mqtt_client, self.prefix)
            )
        if config["lacrosse"].getboolean("enabled"):
            self.components.append(
                lacrosse.LaCrosse(self.cul, self.mqtt_client, self.prefix)
            )

    def get_mqtt_client(self, mqtt_config):
        mqtt_client = mqtt.Client()
        mqtt_client.enable_logger()
        if "username" in mqtt_config and "password" in mqtt_config:
            mqtt_client.username_pw_set(
                mqtt_config["username"], mqtt_config["password"]
            )
        mqtt_client.on_connect = self.on_connect
        mqtt_client.on_message = self.on_message
        try:
            mqtt_client.connect(
                mqtt_config["host"], int(mqtt_config["port"]), keepalive=60
            )
        except Exception as e:
            logging.error("Could not connect to MQTT broker", e)
            sys.exit(1)
        return mqtt_client

    def on_connect(self, mqtt_client, _userdata, _flags, _rc):
        """The callback for when the MQTT client receives a CONNACK response"""

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        mqtt_client.subscribe(self.prefix + "/#")

    def on_message(self, _client, _userdata, msg):
        """The callback for when a message is received"""

        _, _, component, _ = msg.topic.split("/", 3)

        for c in self.components:
            if component == c.get_component_name():
                c.on_message(msg)
                return

        logging.warning("component %s unknown", msg.topic)
        raise ValueError

    def listen(self):
        self.mqtt_client.loop_forever()
