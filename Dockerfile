FROM python:3.10.17-alpine3.21

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .


CMD ["python3", "main.py"]