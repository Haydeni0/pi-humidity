FROM python:3.10.9-bullseye
WORKDIR /build_workdir

RUN apt-get update

RUN python -m pip install --upgrade pip
# Don't use a pip requirements file so we can easily segment the build

# Typical libraries
RUN python -m pip install numpy==1.23
RUN python -m pip install psycopg2==2.9.5
RUN python -m pip install pandas==1.5.1
RUN python -m pip install matplotlib==3.6.2
RUN python -m pip install plotly==5.11.0
RUN python -m pip install dash==2.7.0
RUN python -m pip install black
RUN python -m pip install pyyaml
# Raspberry pi GPIO and sensor libraries
RUN python -m pip install RPi.GPIO
RUN python -m adafruit-circuitpython-dht==3.7.8

# Requirements for pyopenssl
RUN apt-get install -y build-essential 
RUN apt-get install -y libssl-dev 
RUN apt-get install -y libffi-dev 
RUN apt-get install -y python3-dev 
RUN apt-get install -y cargo 
RUN apt-get install -y pkg-config
RUN python -m pip install pyopenssl
