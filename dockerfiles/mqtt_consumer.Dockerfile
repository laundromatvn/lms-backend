FROM python:3.13.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

COPY scripts/start_mqtt_consumer.sh /app/
RUN chmod +x /app/scripts/start_mqtt_consumer.sh

EXPOSE 8000
