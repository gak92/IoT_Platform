import paho.mqtt.client as paho

def on_connect(client, userdata, flags, rc):
    print("PAHO CONNECTED:", rc)
    client.subscribe("iot/data")

def on_message(client, userdata, msg):
    print(f"PAHO MSG: {msg.topic} {msg.payload.decode()}")

client = paho.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_forever()
