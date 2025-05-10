# Main Flask App
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_mqtt import Mqtt
import json
import logging
from datetime import datetime
logging.basicConfig(level=logging.DEBUG)
#================================================
#               Initializing App
#================================================

# Initialize Falsk App
app = Flask(__name__)
app.config.from_pyfile('config.py')
print("MQTT Config Loaded:", app.config["MQTT_BROKER_URL"], app.config["MQTT_BROKER_PORT"])


# Initialize Database
db = SQLAlchemy(app)

# Initialize MQTT
mqtt = Mqtt()
# try:
#     mqtt = Mqtt(app)
#     print("Initialize MQTT..")
# except Exception as e:
#     print(f"Warning: MQTT broker not available. MQTT will be disabled.\n{e}")

#================================================
#               Database settings 
#================================================

# Define Device Model
class Device(db.Model):
    device_id = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)
    description = db.Column(db.String(200), nullable=True)
    sensordatas = db.relationship('SensorData', back_populates="device")

# Define Sensor Data Model
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.ForeignKey('device.device_id'), nullable=False)
    data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    device = db.relationship('Device', back_populates="sensordatas")

# Create Database Tables
with app.app_context():
    db.create_all()
    # Enable foreign keys enforce
    db.session.execute(text('PRAGMA FOREIGN_KEYS=1'))

#================================================
#                    REST API 
#================================================

# Registering a new device
@app.route('/register', methods=['POST'])
def register_device():
    """Register a new device"""
    data = request.json
    if not data or "device_id" not in data:
        return jsonify({"error": "Device ID required"}), 400
    try:
        new_device = Device(device_id=data["device_id"], description=data.get("description"))
        db.session.add(new_device)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": "sensor_id already exists"}), 400

    return jsonify({"message": "Device registered successfully"}), 201


# Receiving Sensor data via HTTP and added into the database
@app.route('/data', methods=['POST'])
def receive_data():
    """Receive sensor data via HTTP"""
    data = request.json
    if not data or "device_id" not in data or "data" not in data:
        return jsonify({"error": "Invalid request"}), 400
    try:
        new_entry = SensorData(device_id=data["device_id"], data=json.dumps(data["data"]))
        db.session.add(new_entry)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": "Invalid sensor_id"}), 400

    return jsonify({"message": "Data received"}), 200


# Reading sensor data of the registered device by giving device id
@app.route('/data/<device_id>', methods=['GET'])
def get_device_data(device_id):
    """Retrieve sensor data for a device"""
    records = SensorData.query.filter_by(device_id=device_id).all()
    return jsonify([{"device_id": r.device_id, "data": json.loads(r.data)} for r in records])



#================================================
#              Handling MQTT
#================================================
topic = 'iot/data'
print("Registered Topic:", topic)

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    """Subscribe to MQTT topic on connection"""
    print("MQTT Connected Callback triggered")
    if rc == 0:
        print('Connected to MQTT Broker!')
        mqtt.subscribe(topic)
        print(f"Subscribed to topic: {topic}")
    else:
        print('Failed to connect. Error code:', rc)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    """Handle incoming MQTT messages"""
    print("MQTT Message Received!")
    print(f"Topic: {message.topic}")
    print(f"Payload: {message.payload.decode()}")

    with app.app_context():
        try:
            payload = json.loads(message.payload.decode())
            new_entry = SensorData(device_id=payload["device_id"], data=json.dumps(payload["data"]))
            db.session.add(new_entry)
            db.session.commit()
            print(f"Data saved from MQTT: {payload}")
        except Exception as e:
            print(f"Error processing MQTT message: {e}")

mqtt.init_app(app)
print("Initialize MQTT..")

#================================================
#              Main App
#================================================
@app.route('/')
def test():
    return "Simple IoT Platform"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
