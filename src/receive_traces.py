"""This script receives trace data from MQTT by subscribing to a topic"""
import json
from paho.mqtt.client import Client as MqttClient
import datetime
import os


class DataReceiver:
    """This class subscribes to the MQTT and receivces traces"""

    def __init__(self, df_holder, params) -> None:
        """
        Initializes the DataReceiver object

        MQTT variable in params (params["MQTT"]) define whether local, or IBM MQTT is used
        """
        super().__init__()
        self.df_holder = df_holder
        self.params = params

    def run(self):
        """Main method that creates client and executes the rest of the script"""

        # create a client
        client = self.create_client(
            host=os.environ["MQTT_HOST"],
            port=int(os.environ["MQTT_PORT"]),
            username=os.environ["MQTT_USERNAME"],
            password=os.environ["MQTT_PASSWORD"],
            clientid=os.environ["MQTT_CLIENTID"] + "_rec",
            cafile=os.environ["MQTT_CERT"],
        )

        client.loop_forever()

    def create_client(self, host, port, username, password, clientid, cafile=None):
        """Creating an MQTT Client Object"""
        client = MqttClient(clientid)

        if username and password:
            client.username_pw_set(username=username, password=password)

        try:
            client.tls_set(ca_certs=cafile)
        except:
            print("Proceeding without certificate file")

        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.connect(host=host, port=port)
        return client

    def on_connect(self, client, userdata, flags, resultcode):
        """Upon connecting to an MQTT server, subscribe to the topic
        The production topic is 'iot-2/type/OpenEEW/id/+/evt/trace/fmt/json'"""

        topic = "iot-2/type/OpenEEW/id/+/evt/status/fmt/json"
        client.subscribe(topic)

        print(f"✅ Subscribed to sensor data with result code {resultcode}")

    def on_message(self, client, userdata, message):
        """When a message is sent to a subscribed topic,
        decode the message and send it to another method"""
        try:
            decoded_message = str(message.payload.decode("utf-8", "ignore"))
            data = json.loads(decoded_message)

            # get timestamp for the received trace
            dt = datetime.datetime.now(datetime.timezone.utc)
            utc_time = dt.replace(tzinfo=datetime.timezone.utc)
            cloud_t = utc_time.timestamp()

            print(cloud_t - data["cloud_t"])

            self.df_holder.update(data, cloud_t)
        except BaseException as exception:
            print(exception)
