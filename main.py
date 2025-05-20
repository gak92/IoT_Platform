# Main Flask Application

#================================================
#               Importing Libraries
#================================================
from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_mqtt import Mqtt
import json
import logging
import random
import string
from datetime import datetime
from functools import wraps
from flask_login import UserMixin
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
logging.basicConfig(level=logging.DEBUG)


#================================================
#               Initializing App
#================================================

# Initialize Falsk App
app = Flask(__name__)
app.config.from_pyfile('config.py')
print("MQTT Config Loaded:", app.config["MQTT_BROKER_URL"], app.config["MQTT_BROKER_PORT"])

# Initialize login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirects to login page if not authenticated

# Initialize Database
db = SQLAlchemy(app)

# Initialize MQTT
mqtt = Mqtt()

#================================================
#               Login and Logout 
#================================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

bcrypt = Bcrypt(app)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('test'))  # Dashboard
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


#================================================
#               Database settings 
#================================================

# Define Device Model
class Device(db.Model):
    device_id = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)
    description = db.Column(db.String(200), nullable=True)
    sensordatas = db.relationship('SensorData', back_populates="device")
    api_key = db.Column(db.String(50), nullable=False)

# Define Sensor Data Model
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.ForeignKey('device.device_id'), nullable=False)
    data = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    device = db.relationship('Device', back_populates="sensordatas")


# Create User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password


# Create Database Tables
with app.app_context():
    db.create_all()
    # Enable foreign keys enforce
    db.session.execute(text('PRAGMA FOREIGN_KEYS=1'))


#================================================
#                    REST API 
#================================================

# @app.route('/create-admin')
# def create_admin():
#     hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')
#     new_user = User(username="admin", password=hashed_pw)
#     db.session.add(new_user)
#     db.session.commit()
#     return "Admin user created."


def valid_api_key(key):
    device = Device.query.filter_by(api_key=key).first()
    if device == None:
        return False
    return True

def create_api_key(length = 8):
    api_key = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return api_key

# API key Decorator
def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        key = request.args.get('key') or request.headers.get('x-api-key')
        if not valid_api_key(key):
            abort(401)  # Unauthorized
        return view_function(*args, **kwargs)
    return decorated_function


# Registering a new device
@app.route('/register', methods=['POST'])
def register_device():
    """Register a new device"""
    data = request.json
    if not data or "device_id" not in data:
        return jsonify({"error": "Device ID required"}), 400
    try:
        new_device = Device(device_id=data["device_id"], description=data.get("description"), api_key=create_api_key())
        db.session.add(new_device)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": "sensor_id already exists"}), 400

    return jsonify({"message": "Device registered successfully"}), 201


# Registering device using UI
@app.route('/register-ui', methods=['POST'])
@login_required
def register_device_ui():
    device_id = request.form.get("device_id")
    description = request.form.get("description")
    
    if not device_id:
        return "Device ID is required", 400

    existing = Device.query.filter_by(device_id=device_id).first()
    if existing:
        return "Device already exists", 409

    new_device = Device(device_id=device_id, description=description, api_key=create_api_key())
    db.session.add(new_device)
    db.session.commit()
    
    return redirect(url_for('test'))

# Deleting the device
@app.route('/delete/<device_id>', methods=['POST'])
@login_required
def delete_device(device_id):
    device = Device.query.filter_by(device_id=device_id).first()
    if device:
        # Delete all related sensor data first (if cascade isn't configured)
        SensorData.query.filter_by(device_id=device_id).delete()
        db.session.delete(device)
        db.session.commit()
        return redirect(url_for('test'))
    return "Device not found", 404



# Receiving Sensor data via HTTP and added into the database
@app.route('/data', methods=['POST'])
@require_api_key
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
            if not valid_api_key(payload.get("api_key")):
                print("Invalid API Key in MQTT message")
                return
            
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

def parse_time(time):
    return time.strftime('%d-%m-%Y %H:%M:%S')

@app.route('/')
@login_required
def test():
    # devices = Device.query.join(SensorData).order_by(SensorData.timestamp).all()
    devices = Device.query.order_by(Device.device_id).all()
    return render_template('index.html', devices=devices, parse_time=parse_time)


@app.route('/device/<device_id>')
@login_required
def device(device_id):
    device = Device.query.filter_by(device_id=device_id).join(SensorData).order_by(SensorData.timestamp).first()
    print(device)
    return render_template('device.html', device=device, parse_time=parse_time)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0')
