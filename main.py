# Main Flask App
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mqtt import Mqtt
import json

# Initialize Falsk App
app = Flask(__name__)


@app.route('/')
def test():
    return "Testing .. Flask App is working..."

if __name__ == '__main__':
    app.run(debug=True)
