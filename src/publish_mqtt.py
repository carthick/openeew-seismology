"""Simulate devices by sending device data to an MQTT Server"""
import json
from paho.mqtt.client import Client as MqttClient
import os


def run(topic, json_data, params):
    """
    Main method that creates client and executes the rest of the script

    MQTT variable in params (params["MQTT"]) define whether local, or IBM MQTT is used
    """

    # create a client
    client = create_client(
        host=os.environ["MQTT_HOST"],
        port=int(os.environ["MQTT_PORT"]),
        username=os.environ["MQTT_USERNAME"],
        password=os.environ["MQTT_PASSWORD"],
        clientid=os.environ["MQTT_CLIENTID"] + "_pub",
        cafile=os.environ["MQTT_CERT"],
    )

    topic = "iot-2/type/OpenEEW/id/region/evt/" + topic + "/fmt/json"

    publish_json(client, topic, json_data)

    client.disconnect()


def publish_json(client, topic, data):
    """Publish each JSON to a given topic"""

    json_obj = json.dumps(data)

    client.publish(topic, json_obj)


def create_client(host, port, username, password, clientid, cafile=None):
    """Creating an MQTT Client Object"""
    client = MqttClient(clientid)

    if username and password:
        client.username_pw_set(username=username, password=password)

    try:
        client.tls_set(ca_certs=cafile)
    except:
        print("Proceeding without certificate file")

    client.connect(host=host, port=port)
    return client
