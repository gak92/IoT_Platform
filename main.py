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
mqtt = Mqtt(app)

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
    

@app.route('/')
def test():
    return "Testing .. Flask App is working..."

if __name__ == '__main__':
    app.run(debug=True)
