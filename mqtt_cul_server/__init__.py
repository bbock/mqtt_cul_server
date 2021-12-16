import logging
import sys
import threading
import paho.mqtt.client as mqtt
from . import cul
from .protocols import somfy_shutter, intertechno, lacrosse


class MQTT_CUL_Server:
    components = {}

    def __init__(self, config={}):
        self.cul = cul.Cul(config["DEFAULT"]["CUL"])
        self.mqtt_client = self.get_mqtt_client(config["mqtt"])

        # prefix for all MQTT topics
        self.prefix = config["DEFAULT"]["prefix"]

        statedir = config["DEFAULT"]["statedir"] or "state"

        if config["intertechno"].getboolean("enabled"):
            self.components["intertechno"] = intertechno.Intertechno(self.cul, self.mqtt_client, self.prefix, config["intertechno"])
        if config["somfy"].getboolean("enabled"):
            self.components["somfy"] = somfy_shutter.SomfyShutter(self.cul, self.mqtt_client, self.prefix, statedir)
        if config["lacrosse"].getboolean("enabled"):
            self.components["lacrosse"] = lacrosse.LaCrosse(self.cul, self.mqtt_client, self.prefix)

    def get_mqtt_client(self, mqtt_config):
        mqtt_client = mqtt.Client()
        mqtt_client.enable_logger()
        if "username" in mqtt_config and "password" in mqtt_config:
            mqtt_client.username_pw_set(
                mqtt_config["username"], mqtt_config["password"]
            )
        mqtt_client.on_connect = self.on_mqtt_connect
        mqtt_client.on_message = self.on_mqtt_message
        try:
            mqtt_client.connect(
                mqtt_config["host"], int(mqtt_config["port"]), keepalive=60
            )
        except Exception as e:
            logging.error("Could not connect to MQTT broker: %s", e)
            sys.exit(1)
        return mqtt_client

    def on_mqtt_connect(self, mqtt_client, _userdata, _flags, _rc):
        """The callback for when the MQTT client receives a CONNACK response"""
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        mqtt_client.subscribe(self.prefix + "/#")

    def on_mqtt_message(self, _client, _userdata, msg):
        """The callback for when a message is received"""
        try:
            _, _, component, _ = msg.topic.split("/", 3)
        except ValueError:
            logging.warning("cannot parse topic: %s", msg.topic)
            return

        if component in self.components:
            self.components[component].on_message(msg)
        else:
            logging.warning("component %s unknown (topic %s)", component, msg.topic)

    def on_rf_message(self, message):
        """Handle message received via RF"""
        if not message: return
        if message[0:3] == "N01":
            self.components["lacrosse"].on_rf_message(message)
        else:
            logging.info("Can't handle RF message: %s", message)

    def start(self):
        """Start multiple threads to listen for MQTT and RF messages"""
        # thread to listen for MQTT command messages
        mqtt_listener = threading.Thread(target=self.mqtt_client.loop_forever)
        mqtt_listener.start()
        # thread to listen for received RF messages
        cul_listener = threading.Thread(target=self.cul.listen, args=[self.on_rf_message])
        cul_listener.start()
