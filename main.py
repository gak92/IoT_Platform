# Main Flask App
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mqtt import Mqtt
import json

# Initialize Falsk App
app = Flask(__name__)
app.config.from_pyfile('config.py')

# Initialize Database
db = SQLAlchemy(app)

# Initialize MQTT
# mqtt = Mqtt(app)

# Define Device Model
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)


# Define Sensor Data Model
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    data = db.Column(db.Text, nullable=False)

# Create Database Tables
with app.app_context():
    db.create_all()

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

    new_device = Device(device_id=data["device_id"], description=data.get("description"))
    db.session.add(new_device)
    db.session.commit()

    return jsonify({"message": "Device registered successfully"}), 201


# Receiving Sensor data via HTTP and added into the database
@app.route('/data', methods=['POST'])
def receive_data():
    """Receive sensor data via HTTP"""
    data = request.json
    if not data or "device_id" not in data or "data" not in data:
        return jsonify({"error": "Invalid request"}), 400

    new_entry = SensorData(device_id=data["device_id"], data=json.dumps(data["data"]))
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({"message": "Data received"}), 200


# Reading sensor data of the registered device by giving device id
@app.route('/data/<device_id>', methods=['GET'])
def get_device_data(device_id):
    """Retrieve sensor data for a device"""
    records = SensorData.query.filter_by(device_id=device_id).all()
    return jsonify([{"device_id": r.device_id, "data": json.loads(r.data)} for r in records])


@app.route('/')
def test():
    return "Testing .. Flask App is working..."

if __name__ == '__main__':
    app.run(debug=True)
