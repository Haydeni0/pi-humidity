FROM python:3.10.9-bullseye
WORKDIR /build_workdir

RUN apt-get update

RUN python -m pip install --upgrade pip

# Typical libraries
RUN python -m pip install -r ./requirements.txt

# Requirements for pyopenssl (cryptography)
RUN apt-get install -y build-essential libssl-dev libffi-dev python3-dev cargo pkg-config
RUN python -m pip install pyopenssl
