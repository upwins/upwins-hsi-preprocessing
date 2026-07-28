FROM python:3.11-slim

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y python3-pyqt5 \
    && python -m pip install --no-cache-dir -v -r requirements.txt
