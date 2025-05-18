# 🔌 Simple IoT Platform

A lightweight IoT middleware platform built using **Flask**, supporting both **HTTP** and **MQTT** protocols for device registration, data collection, and data visualization. Designed for simulation, testing, and education without requiring physical devices.

---

## 🚀 Features

- 📡 Register and manage simulated IoT devices
- 📬 Receive sensor data via HTTP and MQTT (Mosquitto)
- 📊 View sensor data per device via a web dashboard
- 🗃 Store all data in a lightweight SQLite database
- 📂 API and UI access for device management
- 🔐 Ready for future authentication support (Flask-Login, API keys)

---

## 🛠 Tech Stack

| Component        | Technology             |
|------------------|------------------------|
| Backend Framework| Flask (Python)         |
| Messaging        | MQTT (via Mosquitto)   |
| Database         | SQLite (SQLAlchemy ORM)|
| UI               | Bootstrap 5 (HTML templates) |
| MQTT Client      | Flask-MQTT             |
| Dev Tools        | Postman, MQTTX         |
---

## 📦 Requirements

- Python 3.8+
- Mosquitto MQTT broker
- Postman / MQTTX (for simulating devices)

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/gak92/IoT_Platform/
cd IoT_Platform
```

### 2. Install Dependencies
``` pip install -r requirements.txt ```

### 3. Run the App
``` python main.py ```
Then go to: ``` http://127.0.0.1:5000 ```

## 🧪 Simulating Devices
### HTTP using Postman:
- POST /register
```
{
  "device_id": "sensor_001",
  "description": "Test device"
}
```

- POST /data
```
{
  "device_id": "sensor_001",
  "data": {
    "temperature": 25.5,
    "humidity": 60
  }
}
```

- MQTT using CLI or MQTTX
```
mosquitto_pub -t "iot/data" -m '{"device_id": "sensor_001", "data": {"temperature": 25.5}}'

```

## 🌐 Web Dashboard
- Visit: http://localhost:5000
- View all registered devices
- View data from each device
- Add or delete devices via UI

## 🧹 To Do (Planned Features)
- User authentication (Flask-Login)
-  Role-based access (admin/user)
- Data visualization with charts
- RESTful API documentation with Swagger
- Docker support

## 📝 License
- MIT License – feel free to use, modify, and share!

## 🤝 Contributing
- Fork the repo
- Create your feature branch (git checkout -b feature/new-thing)
- Commit your changes (git commit -am 'Add new thing')
- Push to the branch (git push origin feature/new-thing)
- Create a pull request

