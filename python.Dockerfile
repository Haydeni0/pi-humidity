FROM python:3.10
WORKDIR /pytest

RUN pip install --upgrade pip

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
# Also install Raspberry pi GPIO library
RUN python -m pip install RPi.GPIO
RUN python -m pip install pyyaml